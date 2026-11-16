"""Pure-Python, zero-exec AST-combinator FHIRPath R4 evaluation engine."""

from __future__ import annotations

import math
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

_MAX_DEPTH = 64
_MAX_REGEX_LEN = 512
_TWO_ARGS = 2
_THREE_ARGS = 3
_UCUM_URL = "http://unitsofmeasure.org"

_PRIMITIVE_STR_TYPES = frozenset(
    {
        "string",
        "uri",
        "url",
        "canonical",
        "code",
        "id",
        "oid",
        "uuid",
        "markdown",
        "xhtml",
        "date",
        "dateTime",
        "time",
        "instant",
        "base64Binary",
    }
)
_PRIMITIVE_INT_TYPES = frozenset({"integer", "positiveInt", "unsignedInt"})
_KEYWORDS = frozenset(
    {
        "true",
        "false",
        "div",
        "mod",
        "and",
        "or",
        "xor",
        "implies",
        "is",
        "as",
        "in",
        "contains",
    }
)
_STRING_ESCAPES: dict[str, str] = {
    "'": "'",
    '"': '"',
    "\\": "\\",
    "/": "/",
    "n": "\n",
    "t": "\t",
    "r": "\r",
    "f": "\f",
}


@dataclass(frozen=True, slots=True)
class EvalContext:
    """Immutable evaluation context threaded through FHIRPath combinators."""

    resource: dict[str, Any]
    root_resource: dict[str, Any]
    this_item: Any = None
    index: int = 0
    bundle_index: dict[str, dict[str, Any]] | None = None
    context_item: Any = None

    def with_item(self, item: Any, idx: int) -> EvalContext:
        """Return a child context bound to ``$this`` and ``$index``."""
        return EvalContext(
            resource=self.resource,
            root_resource=self.root_resource,
            this_item=item,
            index=idx,
            bundle_index=self.bundle_index,
            context_item=self.context_item,
        )


CompiledExpr = Callable[[EvalContext, list[Any]], list[Any]]
_FuncHandler = Callable[[EvalContext, list[Any], list[CompiledExpr]], list[Any]]


@dataclass(frozen=True, slots=True)
class _Token:
    kind: str
    value: Any
    pos: int


# ---------------------------------------------------------------------------
# Lexer
# ---------------------------------------------------------------------------


def _read_string(expr: str, start: int) -> tuple[_Token, int]:
    """Read a single-quoted FHIRPath string literal."""
    chars: list[str] = []
    i = start + 1
    n = len(expr)
    while i < n:
        ch = expr[i]
        if ch == "'":
            return _Token("STR", "".join(chars), start), i + 1
        if ch == "\\":
            i += 1
            if i >= n:
                raise ValueError(f"Unterminated escape in string at position {start}")
            esc = expr[i]
            if esc == "u" and i + 4 < n:
                hex_part = expr[i + 1 : i + 5]
                chars.append(chr(int(hex_part, 16)))
                i += 5
                continue
            chars.append(_STRING_ESCAPES.get(esc, esc))
            i += 1
            continue
        chars.append(ch)
        i += 1
    raise ValueError(f"Unterminated string literal at position {start}")


def _read_backtick(expr: str, start: int) -> tuple[_Token, int]:
    """Read a backtick-quoted identifier."""
    end = expr.find("`", start + 1)
    if end == -1:
        raise ValueError(f"Unterminated backtick identifier at position {start}")
    return _Token("IDENT", expr[start + 1 : end], start), end + 1


def _read_number(expr: str, start: int) -> tuple[_Token, int]:
    """Read an integer or decimal literal."""
    n = len(expr)
    i = start
    while i < n and expr[i].isdigit():
        i += 1
    if i + 1 < n and expr[i] == "." and expr[i + 1].isdigit():
        i += 1
        while i < n and expr[i].isdigit():
            i += 1
        return _Token("NUM", float(expr[start:i]), start), i
    return _Token("NUM", int(expr[start:i]), start), i


def _read_date_literal(expr: str, start: int) -> tuple[_Token, int]:
    """Read an ``@...`` date/time literal as a string."""
    n = len(expr)
    i = start + 1
    while i < n and (expr[i].isalnum() or expr[i] in "-:+.T"):
        i += 1
    if i == start + 1:
        raise ValueError(f"Invalid date/time literal at position {start}")
    return _Token("STR", expr[start + 1 : i], start), i


def _read_ident(expr: str, start: int) -> tuple[str, int]:
    """Read an identifier starting at ``start``."""
    n = len(expr)
    i = start
    while i < n and (expr[i].isalnum() or expr[i] == "_"):
        i += 1
    return expr[start:i], i


def _skip_ws_and_comments(expr: str, i: int) -> int:
    """Advance past whitespace and ``//`` or ``/* ... */`` comments."""
    n = len(expr)
    while i < n:
        if expr[i].isspace():
            i += 1
        elif expr.startswith("//", i):
            nl = expr.find("\n", i + 2)
            i = n if nl == -1 else nl + 1
        elif expr.startswith("/*", i):
            end = expr.find("*/", i + 2)
            if end == -1:
                raise ValueError(f"Unterminated block comment at position {i}")
            i = end + 2
        else:
            break
    return i


def _read_var_token(expr: str, i: int) -> tuple[_Token, int]:
    """Read a ``$...`` or ``%...`` variable token."""
    prefix = expr[i]
    kind = "SYS" if prefix == "$" else "ENV"
    if i + 1 < len(expr) and expr[i + 1] == "`":
        tok, nxt = _read_backtick(expr, i + 1)
        return _Token(kind, str(tok.value), i), nxt
    name, nxt = _read_ident(expr, i + 1)
    if not name:
        raise ValueError(f"Expected variable name after {prefix!r} at position {i}")
    return _Token(kind, name, i), nxt


def _read_punct_or_op(expr: str, i: int) -> tuple[_Token, int]:
    """Read a 1- or 2-character operator or punctuation token."""
    two = expr[i : i + 2]
    if two in {"!=", "!~", "<=", ">="}:
        return _Token("OP", two, i), i + 2
    ch = expr[i]
    if ch in ".()[]{},|":
        return _Token(ch, ch, i), i + 1
    if ch in "=<>~+-*/&":
        return _Token("OP", ch, i), i + 1
    raise ValueError(f"Unexpected character {ch!r} at position {i}")


def _tokenize(expr: str) -> list[_Token]:
    """Tokenize a FHIRPath expression."""
    tokens: list[_Token] = []
    n = len(expr)
    i = _skip_ws_and_comments(expr, 0)
    while i < n:
        ch = expr[i]
        if ch == "'":
            tok, i = _read_string(expr, i)
        elif ch == "`":
            tok, i = _read_backtick(expr, i)
        elif ch == "@":
            tok, i = _read_date_literal(expr, i)
        elif ch in "$%":
            tok, i = _read_var_token(expr, i)
        elif ch.isdigit():
            tok, i = _read_number(expr, i)
        elif ch.isalpha() or ch == "_":
            ident, i = _read_ident(expr, i)
            kind = "KW" if ident in _KEYWORDS else "IDENT"
            tok = _Token(kind, ident, i - len(ident))
        else:
            tok, i = _read_punct_or_op(expr, i)
        tokens.append(tok)
        i = _skip_ws_and_comments(expr, i)
    tokens.append(_Token("EOF", "", n))
    return tokens


# ---------------------------------------------------------------------------
# Runtime Helpers (Values, Equality, Types, Paths)
# ---------------------------------------------------------------------------


def _is_num(val: Any) -> bool:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _items_equal(a: Any, b: Any) -> bool:
    """FHIRPath strict equality between two singletons."""
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool) and a is b
    if _is_num(a) and _is_num(b):
        return float(a) == float(b)
    if type(a) is not type(b):
        return False
    return bool(a == b)


def _normalize_ws(text: str) -> str:
    return " ".join(text.split()).lower()


def _items_equiv(a: Any, b: Any) -> bool:
    """FHIRPath equivalence (~) between two singletons."""
    if isinstance(a, str) and isinstance(b, str):
        return _normalize_ws(a) == _normalize_ws(b)
    if isinstance(a, dict) and isinstance(b, dict):
        if a.keys() != b.keys():
            return False
        return all(_lists_equiv(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return _lists_equiv(a, b)
    return _items_equal(a, b)


def _lists_equiv(lhs: Any, rhs: Any) -> bool:
    if not isinstance(lhs, list):
        lhs = [lhs] if lhs is not None else []
    if not isinstance(rhs, list):
        rhs = [rhs] if rhs is not None else []
    if len(lhs) != len(rhs):
        return False
    return all(_items_equiv(x, y) for x, y in zip(lhs, rhs, strict=True))


def _dedup(items: list[Any]) -> list[Any]:
    """Deduplicate a collection preserving order in O(N) for hashables."""
    if len(items) <= 1:
        return list(items)
    out: list[Any] = []
    seen_hashable: set[tuple[str, Any]] = set()
    seen_unhashable: list[Any] = []
    for item in items:
        if isinstance(item, bool):
            key: tuple[str, Any] = ("bool", item)
        elif _is_num(item):
            key = ("num", float(item))
        elif isinstance(item, str):
            key = ("str", item)
        else:
            if not any(_items_equal(item, existing) for existing in seen_unhashable):
                seen_unhashable.append(item)
                out.append(item)
            continue
        if key not in seen_hashable:
            seen_hashable.add(key)
            out.append(item)
    return out


def _in_collection(item: Any, collection: list[Any]) -> bool:
    return any(_items_equal(item, candidate) for candidate in collection)


def _to_bool(items: list[Any]) -> bool | None:
    """Evaluate a FHIRPath collection in a 3-valued boolean context."""
    if not items:
        return None
    if len(items) > 1:
        raise ValueError(f"Expected singleton in boolean context, got {len(items)} items")
    val = items[0]
    if isinstance(val, bool):
        return val
    return True


def _is_truthy(items: list[Any]) -> bool:
    return _to_bool(items) is True


def _matches_type(item: Any, type_name: str) -> bool:
    """Check whether ``item`` conforms to FHIRPath type specifier ``type_name``."""
    short = type_name.rsplit(".", 1)[-1]
    matched = False
    if isinstance(item, bool):
        matched = short.lower() == "boolean"
    elif isinstance(item, int):
        matched = short in _PRIMITIVE_INT_TYPES or short.lower() == "integer"
    elif isinstance(item, float):
        matched = short.lower() == "decimal"
    elif isinstance(item, str):
        matched = short in _PRIMITIVE_STR_TYPES or short.lower() == "string"
    elif isinstance(item, dict):
        rt = item.get("resourceType")
        matched = rt == short if isinstance(rt, str) else _matches_complex_dict_type(item, short)
    return matched


_COMPLEX_HINTS: dict[str, tuple[str, ...]] = {
    "Quantity": ("value", "unit", "system", "code"),
    "Age": ("value", "unit", "system", "code"),
    "Duration": ("value", "unit", "system", "code"),
    "CodeableConcept": ("coding", "text"),
    "Coding": ("system", "code", "display"),
    "Reference": ("reference", "display", "identifier"),
    "Period": ("start", "end"),
    "Range": ("low", "high"),
    "Ratio": ("numerator", "denominator"),
    "Identifier": ("system", "value", "use"),
    "HumanName": ("family", "given", "text"),
    "Address": ("line", "city", "state", "postalCode", "country"),
}


def _matches_complex_dict_type(item: dict[str, Any], short: str) -> bool:
    hints = _COMPLEX_HINTS.get(short)
    if hints is None:
        return False
    return any(k in item for k in hints)


def _extend_value(out: list[Any], val: Any) -> None:
    if val is None:
        return
    if isinstance(val, list):
        out.extend(val)
    else:
        out.append(val)


def _step_field(item: Any, field: str) -> list[Any]:
    """Step ``.field`` on a single item, supporting FHIR choice-type keys."""
    if not isinstance(item, dict):
        return []
    if field in item:
        out: list[Any] = []
        _extend_value(out, item[field])
        return out
    flen = len(field)
    for key, val in item.items():
        if key.startswith(field) and len(key) > flen and key[flen].isupper():
            out = []
            _extend_value(out, val)
            return out
    if field and field[0].isupper() and item.get("resourceType") == field:
        return [item]
    return []


def _step_collection(items: list[Any], field: str) -> list[Any]:
    out: list[Any] = []
    for item in items:
        out.extend(_step_field(item, field))
    return out


# ---------------------------------------------------------------------------
# Built-in Function Implementations
# ---------------------------------------------------------------------------


def _fn_exists(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if not args:
        return [len(focus) > 0]
    if len(args) != 1:
        raise ValueError("exists() takes at most 1 argument")
    pred = args[0]
    return [any(_is_truthy(pred(ctx.with_item(item, i), [item])) for i, item in enumerate(focus))]


def _fn_empty(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("empty() takes 0 arguments")
    return [len(focus) == 0]


def _fn_not(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("not() takes 0 arguments")
    val = _to_bool(focus)
    return [] if val is None else [not val]


def _fn_has_value(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("hasValue() takes 0 arguments")
    if len(focus) != 1:
        return [False]
    item = focus[0]
    return [item is not None and not isinstance(item, (dict, list))]


def _fn_count(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("count() takes 0 arguments")
    return [len(focus)]


def _fn_distinct(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("distinct() takes 0 arguments")
    return _dedup(focus)


def _fn_is_distinct(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("isDistinct() takes 0 arguments")
    return [len(_dedup(focus)) == len(focus)]


def _fn_all_true(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("allTrue() takes 0 arguments")
    return [all(item is True for item in focus)]


def _fn_any_true(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("anyTrue() takes 0 arguments")
    return [any(item is True for item in focus)]


def _fn_all_false(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("allFalse() takes 0 arguments")
    return [all(item is False for item in focus)]


def _fn_any_false(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("anyFalse() takes 0 arguments")
    return [any(item is False for item in focus)]


def _fn_where(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("where() requires 1 argument")
    pred = args[0]
    return [
        item for i, item in enumerate(focus) if _is_truthy(pred(ctx.with_item(item, i), [item]))
    ]


def _fn_select(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("select() requires 1 argument")
    proj = args[0]
    out: list[Any] = []
    for i, item in enumerate(focus):
        out.extend(proj(ctx.with_item(item, i), [item]))
    return out


def _fn_all(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("all() requires 1 argument")
    pred = args[0]
    return [all(_is_truthy(pred(ctx.with_item(item, i), [item])) for i, item in enumerate(focus))]


def _fn_repeat(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("repeat() requires 1 argument")
    proj = args[0]
    result: list[Any] = []
    frontier = list(focus)
    for _ in range(_MAX_DEPTH):
        if not frontier:
            break
        next_frontier: list[Any] = []
        for i, item in enumerate(frontier):
            for produced in proj(ctx.with_item(item, i), [item]):
                if not _in_collection(produced, result):
                    result.append(produced)
                    next_frontier.append(produced)
        frontier = next_frontier
    return result


def _fn_first(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("first() takes 0 arguments")
    return [focus[0]] if focus else []


def _fn_last(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("last() takes 0 arguments")
    return [focus[-1]] if focus else []


def _fn_tail(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("tail() takes 0 arguments")
    return focus[1:] if len(focus) > 1 else []


def _eval_int_arg(ctx: EvalContext, focus: list[Any], arg: CompiledExpr) -> int | None:
    res = arg(ctx, focus)
    if len(res) != 1 or not isinstance(res[0], int) or isinstance(res[0], bool):
        return None
    return res[0]


def _eval_str_arg(ctx: EvalContext, focus: list[Any], arg: CompiledExpr) -> str | None:
    res = arg(ctx, focus)
    if len(res) != 1 or not isinstance(res[0], str):
        return None
    return res[0]


def _fn_skip(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("skip() requires 1 argument")
    num = _eval_int_arg(ctx, focus, args[0])
    if num is None:
        return []
    return list(focus) if num <= 0 else focus[num:]


def _fn_take(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("take() requires 1 argument")
    num = _eval_int_arg(ctx, focus, args[0])
    if num is None or num <= 0:
        return []
    return focus[:num]


def _fn_single(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("single() takes 0 arguments")
    if len(focus) > 1:
        raise ValueError(f"single() expected at most 1 item, got {len(focus)}")
    return list(focus)


def _fn_iif(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) not in (_TWO_ARGS, _THREE_ARGS):
        raise ValueError("iif() requires 2 or 3 arguments")
    if _is_truthy(args[0](ctx, focus)):
        return args[1](ctx, focus)
    return args[2](ctx, focus) if len(args) == _THREE_ARGS else []


def _singleton_str(focus: list[Any]) -> str | None:
    if len(focus) != 1 or not isinstance(focus[0], str):
        return None
    return focus[0]


def _fn_matches(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("matches() requires 1 argument")
    s = _singleton_str(focus)
    pat = _eval_str_arg(ctx, focus, args[0])
    if s is None or pat is None:
        return []
    if len(pat) > _MAX_REGEX_LEN:
        raise ValueError("Regex pattern exceeds maximum allowed length")
    try:
        return [re.fullmatch(pat, s) is not None]
    except re.error as exc:
        raise ValueError(f"Invalid regex {pat!r}: {exc}") from exc


def _fn_replace_matches(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != _TWO_ARGS:
        raise ValueError("replaceMatches() requires 2 arguments")
    s = _singleton_str(focus)
    pat = _eval_str_arg(ctx, focus, args[0])
    sub = _eval_str_arg(ctx, focus, args[1])
    if s is None or pat is None or sub is None:
        return []
    if len(pat) > _MAX_REGEX_LEN:
        raise ValueError("Regex pattern exceeds maximum allowed length")
    try:
        return [re.sub(pat, sub, s)]
    except re.error as exc:
        raise ValueError(f"Invalid regex {pat!r}: {exc}") from exc


def _fn_starts_with(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("startsWith() requires 1 argument")
    s = _singleton_str(focus)
    prefix = _eval_str_arg(ctx, focus, args[0])
    return [s.startswith(prefix)] if s is not None and prefix is not None else []


def _fn_ends_with(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("endsWith() requires 1 argument")
    s = _singleton_str(focus)
    suffix = _eval_str_arg(ctx, focus, args[0])
    return [s.endswith(suffix)] if s is not None and suffix is not None else []


def _fn_contains_str(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("contains() requires 1 argument")
    s = _singleton_str(focus)
    sub = _eval_str_arg(ctx, focus, args[0])
    return [sub in s] if s is not None and sub is not None else []


def _fn_substring(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) not in (1, 2):
        raise ValueError("substring() requires 1 or 2 arguments")
    s = _singleton_str(focus)
    start = _eval_int_arg(ctx, focus, args[0])
    if s is None or start is None or start < 0 or start >= len(s):
        return []
    if len(args) == 1:
        return [s[start:]]
    length = _eval_int_arg(ctx, focus, args[1])
    if length is None or length < 0:
        return []
    return [s[start : start + length]]


def _fn_length(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("length() takes 0 arguments")
    s = _singleton_str(focus)
    return [len(s)] if s is not None else []


def _fn_upper(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("upper() takes 0 arguments")
    s = _singleton_str(focus)
    return [s.upper()] if s is not None else []


def _fn_lower(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("lower() takes 0 arguments")
    s = _singleton_str(focus)
    return [s.lower()] if s is not None else []


def _fn_to_chars(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("toChars() takes 0 arguments")
    s = _singleton_str(focus)
    return list(s) if s is not None else []


def _fn_to_integer(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("toInteger() takes 0 arguments")
    if len(focus) != 1:
        return []
    val = focus[0]
    if isinstance(val, bool):
        return [1 if val else 0]
    if isinstance(val, int):
        return [val]
    if isinstance(val, str) and re.fullmatch(r"[+-]?\d+", val):
        return [int(val)]
    return []


def _fn_to_decimal(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("toDecimal() takes 0 arguments")
    if len(focus) != 1:
        return []
    val = focus[0]
    if isinstance(val, bool):
        return [1.0 if val else 0.0]
    if _is_num(val):
        return [float(val)]
    if isinstance(val, str) and re.fullmatch(r"[+-]?\d+(?:\.\d+)?", val):
        return [float(val)]
    return []


def _fn_to_string(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("toString() takes 0 arguments")
    if len(focus) != 1:
        return []
    val = focus[0]
    if isinstance(val, bool):
        return ["true" if val else "false"]
    if isinstance(val, (int, float, str)):
        return [str(val)]
    return []


def _fn_converts_to_integer(
    ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]
) -> list[Any]:
    if args:
        raise ValueError("convertsToInteger() takes 0 arguments")
    if len(focus) != 1:
        return []
    return [len(_fn_to_integer(ctx, focus, [])) == 1]


def _fn_converts_to_decimal(
    ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]
) -> list[Any]:
    if args:
        raise ValueError("convertsToDecimal() takes 0 arguments")
    if len(focus) != 1:
        return []
    return [len(_fn_to_decimal(ctx, focus, [])) == 1]


@dataclass(frozen=True, slots=True)
class _TypeSpecNode:
    type_name: str

    def __call__(self, _ctx: EvalContext, _focus: list[Any]) -> list[Any]:
        return []


def _extract_type_name(arg: CompiledExpr) -> str:
    """Extract the type name from a compiled type-specifier argument."""
    if isinstance(arg, _TypeSpecNode):
        return arg.type_name
    raise ValueError("Expected type specifier argument")


def _fn_is(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("is() requires 1 type argument")
    if not focus:
        return []
    if len(focus) > 1:
        raise ValueError("is() requires singleton input")
    return [_matches_type(focus[0], _extract_type_name(args[0]))]


def _fn_as(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("as() requires 1 type argument")
    tname = _extract_type_name(args[0])
    return [item for item in focus if _matches_type(item, tname)]


def _fn_of_type(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("ofType() requires 1 type argument")
    tname = _extract_type_name(args[0])
    return [item for item in focus if _matches_type(item, tname)]


def _item_children(item: Any) -> list[Any]:
    if not isinstance(item, dict):
        return []
    out: list[Any] = []
    for k, v in item.items():
        if k == "resourceType":
            continue
        _extend_value(out, v)
    return out


def _fn_children(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("children() takes 0 arguments")
    out: list[Any] = []
    for item in focus:
        out.extend(_item_children(item))
    return out


def _fn_descendants(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("descendants() takes 0 arguments")
    out: list[Any] = []
    frontier = list(focus)
    for _ in range(_MAX_DEPTH):
        if not frontier:
            break
        next_frontier: list[Any] = []
        for item in frontier:
            children = _item_children(item)
            out.extend(children)
            next_frontier.extend(children)
        frontier = next_frontier
    return out


def _fn_intersect(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("intersect() requires 1 argument")
    other = args[0](ctx, focus)
    return _dedup([x for x in focus if _in_collection(x, other)])


def _fn_union(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("union() requires 1 argument")
    other = args[0](ctx, focus)
    return _dedup([*focus, *other])


def _fn_exclude(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("exclude() requires 1 argument")
    other = args[0](ctx, focus)
    return [x for x in focus if not _in_collection(x, other)]


def _fn_subset_of(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("subsetOf() requires 1 argument")
    other = args[0](ctx, focus)
    return [all(_in_collection(x, other) for x in focus)]


def _fn_superset_of(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("supersetOf() requires 1 argument")
    other = args[0](ctx, focus)
    return [all(_in_collection(x, focus) for x in other)]


def _fn_trace(_ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) not in (1, 2):
        raise ValueError("trace() requires 1 or 2 arguments")
    return list(focus)


def _fn_extension(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if len(args) != 1:
        raise ValueError("extension() requires 1 argument")
    url = _eval_str_arg(ctx, focus, args[0])
    if url is None:
        return []
    out: list[Any] = []
    for item in focus:
        if not isinstance(item, dict):
            continue
        exts = item.get("extension")
        if isinstance(exts, list):
            out.extend(e for e in exts if isinstance(e, dict) and e.get("url") == url)
    return out


def _resolve_single_ref(ctx: EvalContext, item: Any) -> dict[str, Any] | None:
    ref: Any = item.get("reference") if isinstance(item, dict) else item
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("#") and len(ref) > 1:
        target_id = ref[1:]
        for container in (ctx.resource, ctx.root_resource):
            for c in container.get("contained") or []:
                if isinstance(c, dict) and c.get("id") == target_id:
                    return c
        return None
    if ctx.bundle_index is not None:
        return ctx.bundle_index.get(ref)
    return None


def _fn_resolve(ctx: EvalContext, focus: list[Any], args: list[CompiledExpr]) -> list[Any]:
    if args:
        raise ValueError("resolve() takes 0 arguments")
    out: list[Any] = []
    for item in focus:
        resolved = _resolve_single_ref(ctx, item)
        if resolved is not None:
            out.append(resolved)
    return out


_FUNCTIONS: dict[str, _FuncHandler] = {
    "exists": _fn_exists,
    "empty": _fn_empty,
    "not": _fn_not,
    "hasValue": _fn_has_value,
    "count": _fn_count,
    "distinct": _fn_distinct,
    "isDistinct": _fn_is_distinct,
    "allTrue": _fn_all_true,
    "anyTrue": _fn_any_true,
    "allFalse": _fn_all_false,
    "anyFalse": _fn_any_false,
    "where": _fn_where,
    "select": _fn_select,
    "all": _fn_all,
    "repeat": _fn_repeat,
    "first": _fn_first,
    "last": _fn_last,
    "tail": _fn_tail,
    "skip": _fn_skip,
    "take": _fn_take,
    "single": _fn_single,
    "iif": _fn_iif,
    "matches": _fn_matches,
    "replaceMatches": _fn_replace_matches,
    "startsWith": _fn_starts_with,
    "endsWith": _fn_ends_with,
    "contains": _fn_contains_str,
    "substring": _fn_substring,
    "length": _fn_length,
    "upper": _fn_upper,
    "lower": _fn_lower,
    "toChars": _fn_to_chars,
    "toInteger": _fn_to_integer,
    "toDecimal": _fn_to_decimal,
    "toString": _fn_to_string,
    "convertsToInteger": _fn_converts_to_integer,
    "convertsToDecimal": _fn_converts_to_decimal,
    "is": _fn_is,
    "as": _fn_as,
    "ofType": _fn_of_type,
    "children": _fn_children,
    "descendants": _fn_descendants,
    "intersect": _fn_intersect,
    "union": _fn_union,
    "exclude": _fn_exclude,
    "subsetOf": _fn_subset_of,
    "supersetOf": _fn_superset_of,
    "trace": _fn_trace,
    "extension": _fn_extension,
    "resolve": _fn_resolve,
}


# ---------------------------------------------------------------------------
# Operator Combinator Builders
# ---------------------------------------------------------------------------


def _eval_num_op(op: str, a: int | float, b: int | float) -> Any:
    res: Any = None
    if op == "+":
        res = a + b
    elif op == "-":
        res = a - b
    elif op == "*":
        res = a * b
    elif b != 0:
        if op == "/":
            res = a / b
        elif op == "div":
            res = int(a / b)
        else:
            res = math.fmod(a, b) if isinstance(a, float) or isinstance(b, float) else a % b
    return res


def _make_arith(op: str, lhs: CompiledExpr, rhs: CompiledExpr) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        lval = lhs(ctx, focus)
        rval = rhs(ctx, focus)
        if op == "&":
            ls = str(lval[0]) if len(lval) == 1 else ""
            rs = str(rval[0]) if len(rval) == 1 else ""
            return [ls + rs]
        if len(lval) != 1 or len(rval) != 1:
            return []
        a, b = lval[0], rval[0]
        if op == "+" and isinstance(a, str) and isinstance(b, str):
            return [a + b]
        if not (_is_num(a) and _is_num(b)):
            return []
        res = _eval_num_op(op, a, b)
        if res is None:
            return []
        is_int_op = op in {"+", "-", "*", "mod"} and isinstance(a, int) and isinstance(b, int)
        return [int(res)] if is_int_op else [res]

    return _eval


def _make_cmp(op: str, lhs: CompiledExpr, rhs: CompiledExpr) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        lval = lhs(ctx, focus)
        rval = rhs(ctx, focus)
        if len(lval) != 1 or len(rval) != 1:
            return []
        a, b = lval[0], rval[0]
        if not ((_is_num(a) and _is_num(b)) or (isinstance(a, str) and isinstance(b, str))):
            return []
        if op == "<":
            return [a < b]
        if op == "<=":
            return [a <= b]
        if op == ">":
            return [a > b]
        return [a >= b]

    return _eval


def _make_eq(op: str, lhs: CompiledExpr, rhs: CompiledExpr) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        lval = lhs(ctx, focus)
        rval = rhs(ctx, focus)
        if op in {"~", "!~"}:
            eq = _lists_equiv(lval, rval)
            return [eq] if op == "~" else [not eq]
        if not lval or not rval:
            return []
        if len(lval) != len(rval):
            eq = False
        else:
            eq = all(_items_equal(a, b) for a, b in zip(lval, rval, strict=True))
        return [eq] if op == "=" else [not eq]

    return _eval


def _make_membership(op: str, lhs: CompiledExpr, rhs: CompiledExpr) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        lval = lhs(ctx, focus)
        rval = rhs(ctx, focus)
        if op == "in":
            if not lval:
                return []
            if len(lval) > 1:
                raise ValueError("Left side of 'in' must be a singleton")
            return [_in_collection(lval[0], rval)]
        if not rval:
            return []
        if len(rval) > 1:
            raise ValueError("Right side of 'contains' must be a singleton")
        return [_in_collection(rval[0], lval)]

    return _eval


def _eval_implies(
    lb: bool | None, rhs: CompiledExpr, ctx: EvalContext, focus: list[Any]
) -> list[Any]:
    if lb is None or lb is False:
        return [True]
    rb = _to_bool(rhs(ctx, focus))
    return [] if rb is None else [rb]


def _eval_and(lb: bool | None, rhs: CompiledExpr, ctx: EvalContext, focus: list[Any]) -> list[Any]:
    if lb is False:
        return [False]
    rb = _to_bool(rhs(ctx, focus))
    if rb is False:
        return [False]
    return [True] if (lb is True and rb is True) else []


def _eval_or(lb: bool | None, rhs: CompiledExpr, ctx: EvalContext, focus: list[Any]) -> list[Any]:
    if lb is True:
        return [True]
    rb = _to_bool(rhs(ctx, focus))
    if rb is True:
        return [True]
    return [False] if (lb is False and rb is False) else []


def _eval_xor(lb: bool | None, rhs: CompiledExpr, ctx: EvalContext, focus: list[Any]) -> list[Any]:
    rb = _to_bool(rhs(ctx, focus))
    if lb is None or rb is None:
        return []
    return [lb != rb]


_BOOL_OPS: dict[str, Callable[[bool | None, CompiledExpr, EvalContext, list[Any]], list[Any]]] = {
    "implies": _eval_implies,
    "and": _eval_and,
    "or": _eval_or,
    "xor": _eval_xor,
}


def _make_bool_op(op: str, lhs: CompiledExpr, rhs: CompiledExpr) -> CompiledExpr:
    fn = _BOOL_OPS[op]

    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        return fn(_to_bool(lhs(ctx, focus)), rhs, ctx, focus)

    return _eval


def _make_union(lhs: CompiledExpr, rhs: CompiledExpr) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        return _dedup([*lhs(ctx, focus), *rhs(ctx, focus)])

    return _eval


def _make_type_op(op: str, lhs: CompiledExpr, type_name: str) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        val = lhs(ctx, focus)
        if not val:
            return []
        if len(val) > 1:
            raise ValueError(f"'{op}' requires singleton input")
        matched = _matches_type(val[0], type_name)
        if op == "is":
            return [matched]
        return [val[0]] if matched else []

    return _eval


# ---------------------------------------------------------------------------
# Recursive-Descent Parser -> Combinators
# ---------------------------------------------------------------------------


class _Parser:
    def __init__(self, tokens: list[_Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> _Token:
        return self.tokens[self.pos]

    def advance(self) -> _Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def expect(self, kind: str) -> _Token:
        tok = self.peek()
        if tok.kind != kind:
            raise ValueError(f"Expected {kind}, got {tok.kind} ({tok.value!r}) at pos {tok.pos}")
        return self.advance()

    def parse(self) -> CompiledExpr:
        expr = self._parse_implies()
        if self.peek().kind != "EOF":
            tok = self.peek()
            raise ValueError(f"Unexpected token {tok.value!r} at pos {tok.pos}")
        return expr

    def _parse_implies(self) -> CompiledExpr:
        node = self._parse_or_xor()
        while self.peek().kind == "KW" and self.peek().value == "implies":
            self.advance()
            rhs = self._parse_or_xor()
            node = _make_bool_op("implies", node, rhs)
        return node

    def _parse_or_xor(self) -> CompiledExpr:
        node = self._parse_and()
        while self.peek().kind == "KW" and self.peek().value in {"or", "xor"}:
            op = str(self.advance().value)
            rhs = self._parse_and()
            node = _make_bool_op(op, node, rhs)
        return node

    def _parse_and(self) -> CompiledExpr:
        node = self._parse_membership()
        while self.peek().kind == "KW" and self.peek().value == "and":
            self.advance()
            rhs = self._parse_membership()
            node = _make_bool_op("and", node, rhs)
        return node

    def _parse_membership(self) -> CompiledExpr:
        node = self._parse_equality()
        while self.peek().kind == "KW" and self.peek().value in {"in", "contains"}:
            op = str(self.advance().value)
            rhs = self._parse_equality()
            node = _make_membership(op, node, rhs)
        return node

    def _parse_equality(self) -> CompiledExpr:
        node = self._parse_comparison()
        while self.peek().kind == "OP" and self.peek().value in {"=", "!=", "~", "!~"}:
            op = str(self.advance().value)
            rhs = self._parse_comparison()
            node = _make_eq(op, node, rhs)
        return node

    def _parse_comparison(self) -> CompiledExpr:
        node = self._parse_union()
        while self.peek().kind == "OP" and self.peek().value in {"<", "<=", ">", ">="}:
            op = str(self.advance().value)
            rhs = self._parse_union()
            node = _make_cmp(op, node, rhs)
        return node

    def _parse_union(self) -> CompiledExpr:
        node = self._parse_type_op()
        while self.peek().kind == "|":
            self.advance()
            rhs = self._parse_type_op()
            node = _make_union(node, rhs)
        return node

    def _parse_type_op(self) -> CompiledExpr:
        node = self._parse_additive()
        while self.peek().kind == "KW" and self.peek().value in {"is", "as"}:
            op = str(self.advance().value)
            tname = self._parse_type_specifier()
            node = _make_type_op(op, node, tname)
        return node

    def _parse_type_specifier(self) -> str:
        tok = self.peek()
        if tok.kind not in {"IDENT", "KW"}:
            raise ValueError(f"Expected type specifier at pos {tok.pos}")
        parts = [str(self.advance().value)]
        while self.peek().kind == ".":
            self.advance()
            nxt = self.peek()
            if nxt.kind not in {"IDENT", "KW"}:
                raise ValueError(f"Expected identifier after '.' in type at pos {nxt.pos}")
            parts.append(str(self.advance().value))
        return ".".join(parts)

    def _parse_additive(self) -> CompiledExpr:
        node = self._parse_multiplicative()
        while self.peek().kind == "OP" and self.peek().value in {"+", "-", "&"}:
            op = str(self.advance().value)
            rhs = self._parse_multiplicative()
            node = _make_arith(op, node, rhs)
        return node

    def _parse_multiplicative(self) -> CompiledExpr:
        node = self._parse_unary()
        while (self.peek().kind == "OP" and self.peek().value in {"*", "/"}) or (
            self.peek().kind == "KW" and self.peek().value in {"div", "mod"}
        ):
            op = str(self.advance().value)
            rhs = self._parse_unary()
            node = _make_arith(op, node, rhs)
        return node

    def _parse_unary(self) -> CompiledExpr:
        if self.peek().kind == "OP" and self.peek().value in {"+", "-"}:
            op = str(self.advance().value)
            operand = self._parse_unary()

            def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
                res = operand(ctx, focus)
                if len(res) != 1 or not _is_num(res[0]):
                    return []
                return [res[0]] if op == "+" else [-res[0]]

            return _eval
        return self._parse_postfix()

    def _parse_postfix(self) -> CompiledExpr:
        node = self._parse_primary()
        while True:
            if self.peek().kind == ".":
                self.advance()
                node = self._parse_dot_suffix(node)
            elif self.peek().kind == "[":
                self.advance()
                idx_expr = self._parse_implies()
                self.expect("]")
                node = _make_indexer(node, idx_expr)
            else:
                break
        return node

    def _parse_dot_suffix(self, target: CompiledExpr) -> CompiledExpr:
        tok = self.peek()
        if tok.kind not in {"IDENT", "KW"}:
            raise ValueError(f"Expected member or function after '.' at pos {tok.pos}")
        name = str(self.advance().value)
        if self.peek().kind == "(":
            args = self._parse_arg_list(name)
            fn = _resolve_function(name)
            return lambda ctx, focus: fn(ctx, target(ctx, focus), args)
        return lambda ctx, focus: _step_collection(target(ctx, focus), name)

    def _parse_arg_list(self, fn_name: str) -> list[CompiledExpr]:
        self.expect("(")
        args: list[CompiledExpr] = []
        if self.peek().kind != ")":
            if fn_name in {"is", "as", "ofType"}:
                tname = self._parse_type_specifier()
                args.append(_make_type_spec_node(tname))
            else:
                args.append(self._parse_implies())
            while self.peek().kind == ",":
                self.advance()
                args.append(self._parse_implies())
        self.expect(")")
        return args

    def _parse_primary(self) -> CompiledExpr:
        tok = self.peek()
        if tok.kind in {"STR", "NUM"} or (tok.kind == "KW" and tok.value in {"true", "false"}):
            val = self.advance().value
            lit: Any = (val == "true") if tok.kind == "KW" else val

            def _lit(_ctx: EvalContext, _focus: list[Any]) -> list[Any]:
                return [lit]

            return _lit
        if tok.kind == "{":
            self.advance()
            self.expect("}")
            return lambda _ctx, _focus: []
        if tok.kind in {"SYS", "ENV"}:
            return _make_var_node(self.advance())
        if tok.kind == "(":
            self.advance()
            inner = self._parse_implies()
            self.expect(")")
            return inner
        if tok.kind == "IDENT" or (
            tok.kind == "KW"
            and tok.value in {"is", "as", "contains"}
            and self.pos + 1 < len(self.tokens)
            and self.tokens[self.pos + 1].kind == "("
        ):
            name = str(self.advance().value)
            if self.peek().kind == "(":
                args = self._parse_arg_list(name)
                fn = _resolve_function(name)
                return lambda ctx, focus: fn(ctx, focus, args)
            return lambda _ctx, focus: _step_collection(focus, name)
        raise ValueError(f"Unexpected token {tok.value!r} at pos {tok.pos}")


def _resolve_function(name: str) -> _FuncHandler:
    fn = _FUNCTIONS.get(name)
    if fn is None:
        raise ValueError(f"Unsupported FHIRPath function: {name}()")
    return fn


def _make_type_spec_node(type_name: str) -> CompiledExpr:
    return _TypeSpecNode(type_name)


def _make_indexer(target: CompiledExpr, idx_expr: CompiledExpr) -> CompiledExpr:
    def _eval(ctx: EvalContext, focus: list[Any]) -> list[Any]:
        items = target(ctx, focus)
        idx_res = idx_expr(ctx, focus)
        if len(idx_res) != 1 or not isinstance(idx_res[0], int) or isinstance(idx_res[0], bool):
            return []
        idx = idx_res[0]
        return [items[idx]] if 0 <= idx < len(items) else []

    return _eval


def _make_var_node(tok: _Token) -> CompiledExpr:
    name = str(tok.value)
    if tok.kind == "SYS":
        if name == "this":
            return lambda ctx, focus: [ctx.this_item] if ctx.this_item is not None else list(focus)
        if name == "index":
            return lambda ctx, _focus: [ctx.index]
        raise ValueError(f"Unsupported system variable: ${name}")
    if name == "resource":
        return lambda ctx, _focus: [ctx.resource] if ctx.resource else []
    if name == "rootResource":
        return lambda ctx, _focus: [ctx.root_resource] if ctx.root_resource else []
    if name == "context":
        return lambda ctx, focus: (
            [ctx.context_item] if ctx.context_item is not None else list(focus)
        )
    if name == "ucum":
        return lambda _ctx, _focus: [_UCUM_URL]
    raise ValueError(f"Unsupported environment variable: %{name}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


@lru_cache(maxsize=2048)
def compile_fhirpath(expr: str) -> CompiledExpr:
    """Compile a FHIRPath expression into a zero-exec AST combinator."""
    if not expr.strip():
        raise ValueError("FHIRPath expression must be a non-empty string")
    tokens = _tokenize(expr)
    return _Parser(tokens).parse()


def _to_focus_list(focus: Any) -> list[Any]:
    if focus is None:
        return []
    if isinstance(focus, list):
        return list(focus)
    return [focus]


def evaluate_fhirpath(
    expr: str,
    focus: Any,
    *,
    resource: dict[str, Any] | None = None,
    root_resource: dict[str, Any] | None = None,
    bundle_index: dict[str, dict[str, Any]] | None = None,
) -> list[Any]:
    """Evaluate a FHIRPath expression against ``focus`` and return a result list."""
    compiled = compile_fhirpath(expr)
    res_dict = resource if resource is not None else (focus if isinstance(focus, dict) else {})
    root_dict = root_resource if root_resource is not None else res_dict
    ctx = EvalContext(
        resource=res_dict,
        root_resource=root_dict,
        bundle_index=bundle_index,
        context_item=focus,
    )
    return compiled(ctx, _to_focus_list(focus))


def evaluate_compiled_invariant(
    compiled: CompiledExpr,
    focus: Any,
    ctx: EvalContext,
) -> bool:
    """Evaluate a pre-compiled FHIRPath invariant; returns False only if non-empty and all-False."""
    try:
        result = compiled(ctx, _to_focus_list(focus))
    except ValueError:
        return True
    if not result:
        return True
    return not all(item is False for item in result)


def evaluate_fhirpath_invariant(
    expr: str,
    focus: Any,
    *,
    ctx: EvalContext | None = None,
    strict: bool = False,
) -> bool:
    """Evaluate a FHIR invariant; returns False only if non-empty and all-False."""
    try:
        compiled = compile_fhirpath(expr)
        if ctx is None:
            res_dict = focus if isinstance(focus, dict) else {}
            ctx = EvalContext(resource=res_dict, root_resource=res_dict, context_item=focus)
        result = compiled(ctx, _to_focus_list(focus))
    except ValueError:
        if strict:
            raise
        return True
    if not result:
        return True
    return not all(item is False for item in result)
