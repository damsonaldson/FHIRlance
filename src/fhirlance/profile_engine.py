"""Compiled IG StructureDefinition profile engine."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise
from typing import Any
from urllib.parse import urlsplit

from fhirlance.fhirpath import (
    CompiledExpr,
    EvalContext,
    compile_fhirpath,
    evaluate_compiled_invariant,
)
from fhirlance.profiles import COMPLETE_CODE_SYSTEMS, PROFILE_CONSTRAINTS, VALUE_SET_SPECS
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.terminology import (
    TxOptions,
    _normalize_vs_spec,
    parse_tx_options,
    validate_binding_value,
)

_CHOICE_SUFFIX = "[x]"
_CHOICE_SUFFIX_LEN = len(_CHOICE_SUFFIX)
_CONTAINED_CONSTRAINT_KEYS = frozenset({"dom-2", "dom-3", "dom-4", "dom-5"})


@dataclass(frozen=True, slots=True)
class PathRule:
    """A constraint referencing a single dotted FHIR element path."""

    path: str
    parts: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValueRule:
    """A fixed[x] or pattern[x] constraint on a FHIR element path."""

    path: str
    parts: tuple[str, ...]
    expected: Any


@dataclass(frozen=True, slots=True)
class MaxLengthRule:
    """A maxLength constraint on a string/primitive FHIR element path."""

    path: str
    parts: tuple[str, ...]
    max_length: int


@dataclass(frozen=True, slots=True)
class ValueBoundsRule:
    """A minValue[x] / maxValue[x] constraint on a FHIR element path."""

    path: str
    parts: tuple[str, ...]
    min_val: Any = None
    max_val: Any = None


@dataclass(frozen=True, slots=True)
class AllowedValuesRule:
    """A Reference targetProfile or required ValueSet binding rule."""

    path: str
    parts: tuple[str, ...]
    allowed: frozenset[str]


@dataclass(frozen=True, slots=True)
class TypeNarrowingRule:
    """A choice-type [x] narrowing constraint from a profile snapshot/differential."""

    path: str
    parent_parts: tuple[str, ...]
    stem: str
    allowed_suffixes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SliceMatcher:
    """A discriminator matcher inside a profile slice."""

    sub_parts: tuple[str, ...]
    kind: str
    expected: Any


_FHIR_PRIMITIVE_LOWER: dict[str, str] = {
    "Boolean": "boolean",
    "Integer": "integer",
    "String": "string",
    "Decimal": "decimal",
    "Uri": "uri",
    "Url": "url",
    "Canonical": "canonical",
    "Base64Binary": "base64Binary",
    "Instant": "instant",
    "Date": "date",
    "DateTime": "dateTime",
    "Time": "time",
    "Code": "code",
    "Oid": "oid",
    "Id": "id",
    "Markdown": "markdown",
    "UnsignedInt": "unsignedInt",
    "PositiveInt": "positiveInt",
    "Uuid": "uuid",
}
_FHIR_PRIMITIVES: frozenset[str] = frozenset(_FHIR_PRIMITIVE_LOWER.values())
_STR_FHIR_TYPES: frozenset[str] = frozenset(
    {
        "string",
        "uri",
        "url",
        "canonical",
        "base64Binary",
        "instant",
        "date",
        "dateTime",
        "time",
        "code",
        "oid",
        "id",
        "markdown",
        "uuid",
        "xhtml",
    }
)
_INT_FHIR_TYPES: frozenset[str] = frozenset({"integer", "decimal", "unsignedInt", "positiveInt"})


@dataclass(frozen=True, slots=True)
class CompiledSlice:
    """A minimum/maximum-cardinality slice rule with compiled matchers."""

    path: str
    parts: tuple[str, ...]
    min_count: int
    matchers: tuple[SliceMatcher, ...]
    max_count: int | None = None


@dataclass(frozen=True, slots=True)
class SliceDiscriminator:
    """A compiled FHIR StructureDefinition slicing discriminator."""

    kind: str
    path: str
    sub_parts: tuple[str, ...]
    resolve_target: bool


@dataclass(frozen=True, slots=True)
class CompiledSliceRule:
    """A compiled slice definition within a slice group."""

    slice_name: str
    min_count: int
    max_count: int | None
    matchers: tuple[SliceMatcher, ...]
    type_constraints: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]
    profile_constraints: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...]
    exists_constraints: tuple[tuple[tuple[str, ...], bool], ...]
    sub_groups: tuple[CompiledSliceGroup, ...]


@dataclass(frozen=True, slots=True)
class CompiledSliceGroup:
    """A compiled FHIR slicing group with discriminators, rules, and slices."""

    path: str
    parts: tuple[str, ...]
    is_choice: bool
    rules: str
    ordered: bool
    discriminators: tuple[SliceDiscriminator, ...]
    slices: tuple[CompiledSliceRule, ...]


@dataclass(frozen=True, slots=True)
class CompiledBindingRule:
    """A compiled ValueSet binding constraint."""

    path: str
    parts: tuple[str, ...]
    strength: str
    value_set: str
    vs_spec: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CompiledConstraint:
    """A pre-compiled FHIRPath invariant constraint on a StructureDefinition."""

    key: str
    severity: str
    path: str
    parts: tuple[str, ...]
    human: str
    evaluator: CompiledExpr
    requires_contained: bool = False


@dataclass(frozen=True, slots=True)
class CompiledProfile:
    """Pre-compiled StructureDefinition constraint set for fast validation."""

    base_type: str | None
    required: tuple[PathRule, ...]
    forbidden: tuple[PathRule, ...]
    max_one: tuple[PathRule, ...]
    fixed: tuple[ValueRule, ...]
    pattern: tuple[ValueRule, ...]
    type_narrowing: tuple[TypeNarrowingRule, ...]
    target_types: tuple[AllowedValuesRule, ...]
    bindings: tuple[AllowedValuesRule, ...]
    slices: tuple[CompiledSlice, ...]
    binding_specs: tuple[CompiledBindingRule, ...] = ()
    slice_groups: tuple[CompiledSliceGroup, ...] = ()
    target_profiles: tuple[AllowedValuesRule, ...] = ()
    target_aggregations: tuple[AllowedValuesRule, ...] = ()
    constraints: tuple[CompiledConstraint, ...] = ()
    preferred_bindings: tuple[CompiledBindingRule, ...] = ()
    max_length: tuple[MaxLengthRule, ...] = ()
    value_bounds: tuple[ValueBoundsRule, ...] = ()
    element_profiles: tuple[AllowedValuesRule, ...] = ()
    must_support: tuple[PathRule, ...] = ()


def pattern_matches(actual: Any, pattern: Any) -> bool:
    """Return True if `actual` satisfies FHIR pattern[x] subset semantics."""
    if isinstance(pattern, dict):
        if not isinstance(actual, dict):
            return False
        return all(k in actual and pattern_matches(actual[k], v) for k, v in pattern.items())
    if isinstance(pattern, list):
        if not isinstance(actual, list):
            return False
        return all(any(pattern_matches(item, pat) for item in actual) for pat in pattern)
    return bool(actual == pattern)


def _resolve_choice_typed_nodes(
    obj: dict[str, Any], stem: str, tail: list[str]
) -> list[tuple[Any, str | None]]:
    out: list[tuple[Any, str | None]] = []
    for key, value in obj.items():
        if not key.startswith(stem) or key.startswith("_") or value is None:
            continue
        suffix = key[len(stem) :]
        if not suffix or not suffix[0].isupper():
            continue
        if tail:
            out.extend(resolve_typed_nodes(value, tail))
            continue
        inferred = _FHIR_PRIMITIVE_LOWER.get(suffix, suffix)
        if isinstance(value, list):
            out.extend((item, inferred) for item in value if item is not None)
        else:
            out.append((value, inferred))
    return out


def resolve_typed_nodes(
    obj: Any, parts: tuple[str, ...] | list[str]
) -> list[tuple[Any, str | None]]:
    """Resolve all values matching a dotted FHIR path, inferring [x] choice types."""
    if isinstance(obj, list):
        out: list[tuple[Any, str | None]] = []
        for item in obj:
            out.extend(resolve_typed_nodes(item, parts))
        return out
    if not parts:
        return [(obj, None)] if obj is not None else []
    if not isinstance(obj, dict):
        return []

    head, *tail = parts
    if head.endswith(_CHOICE_SUFFIX):
        return _resolve_choice_typed_nodes(obj, head[:-_CHOICE_SUFFIX_LEN], tail)

    val = obj.get(head)
    return resolve_typed_nodes(val, tail) if val is not None else []


def resolve_nodes(obj: Any, parts: tuple[str, ...] | list[str]) -> list[Any]:
    """Resolve all values matching a dotted FHIR path (supporting [x] choice stems)."""
    if isinstance(obj, list):
        out: list[Any] = []
        for item in obj:
            out.extend(resolve_nodes(item, parts))
        return out
    if not parts:
        return [obj] if obj is not None else []
    if not isinstance(obj, dict):
        return []

    head, *tail = parts
    if head.endswith(_CHOICE_SUFFIX):
        stem = head[:-_CHOICE_SUFFIX_LEN]
        out = []
        for key, value in obj.items():
            if key.startswith(stem) and not key.startswith("_") and value is not None:
                out.extend(resolve_nodes(value, tail))
        return out

    if head not in obj or obj[head] is None:
        return []
    return resolve_nodes(obj[head], tail)


def _is_non_empty_value(val: Any) -> bool:
    if val is None:
        return False
    if isinstance(val, list):
        return any(x is not None for x in val)
    return True


def _check_child_present(parent_val: Any, child_seg: str) -> bool:
    if not isinstance(parent_val, dict):
        return False
    if child_seg.endswith(_CHOICE_SUFFIX):
        stem = child_seg[:-_CHOICE_SUFFIX_LEN]
        return any(
            k.startswith(stem) and not k.startswith("_") and _is_non_empty_value(parent_val[k])
            for k in parent_val
        )
    return child_seg in parent_val and _is_non_empty_value(parent_val[child_seg])


def _extract_ref_resource_type(ref_str: str) -> str | None:
    """Extract target resourceType from relative/absolute FHIR Reference strings."""
    if not ref_str or ref_str.startswith(("#", "urn:")):
        return None
    parts = ref_str.split("/")
    for segment in parts[:-1]:
        if segment in RESOURCE_MODELS:
            return segment
    return None


_MIN_REF_PATH_PARTS = 2


def extract_relative_ref(url: str) -> str | None:
    """Extract 'ResourceType/id' from an http(s)://.../{ResourceType}/{id} URL."""
    if not url.startswith(("http://", "https://")):
        return None
    parts = urlsplit(url).path.rstrip("/").split("/")
    if len(parts) < _MIN_REF_PATH_PARTS:
        return None
    rtype, rid = parts[-2], parts[-1]
    if rtype in RESOURCE_MODELS and rid:
        return f"{rtype}/{rid}"
    return None


def _compile_binding_specs(
    base_type: str | None,
    raw_binding_specs: dict[str, Any],
    raw_bindings: dict[str, Any],
) -> tuple[CompiledBindingRule, ...]:
    rules: list[CompiledBindingRule] = []
    seen: set[str] = set()
    for rel_path, b_info in raw_binding_specs.items():
        if base_type and rel_path.startswith(f"{base_type}."):
            full_path = rel_path
            parts = tuple(rel_path.split(".")[1:])
        elif "." in rel_path and not base_type:
            full_path = rel_path
            parts = tuple(p for p in rel_path.split(".") if p)
        else:
            full_path = f"{base_type}.{rel_path}" if base_type else rel_path
            parts = tuple(p for p in rel_path.split(".") if p)
        seen.add(full_path)
        seen.add(rel_path)
        vs_url = b_info.get("value_set", "")
        raw_vs = b_info.get("vs_spec") or VALUE_SET_SPECS.get(vs_url)
        vs_spec = _normalize_vs_spec(raw_vs)
        rules.append(
            CompiledBindingRule(
                path=full_path,
                parts=parts,
                strength=b_info.get("strength", "extensible"),
                value_set=vs_url,
                vs_spec=vs_spec,
            )
        )
    for p, codes in raw_bindings.items():
        rel_p = p.split(".", 1)[1] if "." in p else p
        if p not in seen and rel_p not in seen:
            parts = tuple(p.split(".")[1:] if "." in p else p.split("."))
            rules.append(
                CompiledBindingRule(
                    path=p,
                    parts=parts,
                    strength="required",
                    value_set="urn:fhirlance:inline",
                    vs_spec={"codes": frozenset(codes), "system_codes": {}, "external_systems": []},
                )
            )
    return tuple(rules)


def _parse_max_count(raw: Any) -> int | None:
    if raw is None or raw == "*":
        return None
    if isinstance(raw, int) and not isinstance(raw, bool):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


def _split_sub_parts(rel_sub: str) -> tuple[str, ...]:
    if not rel_sub:
        return ()
    return tuple(seg.split(":")[0] for seg in rel_sub.split(".") if seg)


def _compile_discriminator(raw: dict[str, str]) -> SliceDiscriminator:
    kind = raw["type"]
    path = raw.get("path") or "$this"
    if path == "$this":
        return SliceDiscriminator(kind=kind, path=path, sub_parts=(), resolve_target=False)
    if path == "$this.resolve()":
        return SliceDiscriminator(kind=kind, path=path, sub_parts=(), resolve_target=True)
    resolve_target = path.endswith(".resolve()")
    trimmed = path[: -len(".resolve()")] if resolve_target else path
    sub_parts = tuple(seg for seg in trimmed.split(".") if seg and seg != "$this")
    return SliceDiscriminator(
        kind=kind,
        path=path,
        sub_parts=sub_parts,
        resolve_target=resolve_target,
    )


def _compile_slice_rule(sl: dict[str, Any]) -> CompiledSliceRule:
    return CompiledSliceRule(
        slice_name=sl["slice_name"],
        min_count=int(sl.get("min", 0)),
        max_count=_parse_max_count(sl.get("max")),
        matchers=tuple(
            SliceMatcher(_split_sub_parts(sub), kind, exp)
            for sub, (kind, exp) in sl.get("matchers", {}).items()
        ),
        type_constraints=tuple(
            (_split_sub_parts(sub), tuple(codes))
            for sub, codes in sl.get("type_constraints", {}).items()
        ),
        profile_constraints=tuple(
            (_split_sub_parts(sub), tuple(urls))
            for sub, urls in sl.get("profile_constraints", {}).items()
        ),
        exists_constraints=tuple(
            (_split_sub_parts(sub), bool(flag))
            for sub, flag in sl.get("exists_constraints", {}).items()
        ),
        sub_groups=tuple(
            _compile_slice_group(sg, is_sub_group=True) for sg in sl.get("sub_groups", ())
        ),
    )


def _compile_slice_group(raw: dict[str, Any], *, is_sub_group: bool = False) -> CompiledSliceGroup:
    path = raw["path"]
    segs = path.split(".") if is_sub_group else path.split(".")[1:]
    parts = tuple(seg.split(":")[0] for seg in segs if seg)
    return CompiledSliceGroup(
        path=path,
        parts=parts,
        is_choice=bool(parts and parts[-1].endswith(_CHOICE_SUFFIX)),
        rules=str(raw.get("rules", "open")),
        ordered=bool(raw.get("ordered", False)),
        discriminators=tuple(_compile_discriminator(d) for d in raw.get("discriminators", ())),
        slices=tuple(_compile_slice_rule(sl) for sl in raw.get("slices", ())),
    )


def compile_constraints(
    raw_constraints: list[dict[str, str]] | tuple[dict[str, str], ...],
) -> tuple[CompiledConstraint, ...]:
    """Pre-compile raw ElementDefinition.constraint dicts into CompiledConstraints."""
    compiled: list[CompiledConstraint] = []
    for c in raw_constraints:
        key = str(c.get("key") or "")
        severity = str(c.get("severity") or "")
        expr = str(c.get("expression") or "").strip()
        if not key or not expr or severity not in ("error", "warning"):
            continue
        try:
            evaluator = compile_fhirpath(expr)
        except ValueError:
            continue
        path = str(c.get("path") or "")
        parts = tuple(seg.split(":")[0] for seg in path.split(".")[1:]) if "." in path else ()
        compiled.append(
            CompiledConstraint(
                key=key,
                severity=severity,
                path=path,
                parts=parts,
                human=str(c.get("human") or ""),
                evaluator=evaluator,
                requires_contained=key in _CONTAINED_CONSTRAINT_KEYS,
            )
        )
    return tuple(compiled)


def _compile_preferred_bindings(
    base_type: str | None,
    raw_preferred: dict[str, Any],
) -> tuple[CompiledBindingRule, ...]:
    if not raw_preferred:
        return ()
    raw_specs: dict[str, Any] = {}
    for rel_path, raw_val in raw_preferred.items():
        if isinstance(raw_val, dict):
            raw_specs[rel_path] = {
                "strength": "preferred",
                "value_set": raw_val.get("value_set", ""),
                "vs_spec": raw_val.get("vs_spec"),
            }
        else:
            raw_specs[rel_path] = {"strength": "preferred", "value_set": str(raw_val)}
    return _compile_binding_specs(base_type, raw_specs, {})


def _compile_value_bounds(
    min_values: dict[str, Any], max_values: dict[str, Any]
) -> tuple[ValueBoundsRule, ...]:
    all_paths = sorted(set(min_values) | set(max_values))
    return tuple(
        ValueBoundsRule(
            path=p,
            parts=tuple(p.split(".")[1:]),
            min_val=min_values.get(p),
            max_val=max_values.get(p),
        )
        for p in all_paths
    )


def _compile_single_profile(spec: dict[str, Any]) -> CompiledProfile:
    base_type = spec.get("base_type")
    return CompiledProfile(
        base_type=base_type,
        required=tuple(PathRule(p, tuple(p.split(".")[1:])) for p in spec.get("required", ())),
        forbidden=tuple(PathRule(p, tuple(p.split(".")[1:])) for p in spec.get("forbidden", ())),
        max_one=tuple(PathRule(p, tuple(p.split(".")[1:])) for p in spec.get("max_one", ())),
        fixed=tuple(
            ValueRule(p, tuple(p.split(".")[1:]), exp) for p, exp in spec.get("fixed", {}).items()
        ),
        pattern=tuple(
            ValueRule(p, tuple(p.split(".")[1:]), pat) for p, pat in spec.get("pattern", {}).items()
        ),
        type_narrowing=tuple(
            TypeNarrowingRule(
                path=p,
                parent_parts=tuple(p.split(".")[1:-1]),
                stem=p.split(".")[-1][:-_CHOICE_SUFFIX_LEN],
                allowed_suffixes=tuple(t[0].upper() + t[1:] for t in types),
            )
            for p, types in spec.get("type_narrowing", {}).items()
            if p.endswith(_CHOICE_SUFFIX)
        ),
        target_types=tuple(
            AllowedValuesRule(p, tuple(p.split(".")[1:]), frozenset(types))
            for p, types in spec.get("target_types", {}).items()
            if "Resource" not in types
        ),
        bindings=tuple(
            AllowedValuesRule(p, tuple(p.split(".")[1:]), frozenset(codes))
            for p, codes in spec.get("bindings", {}).items()
        ),
        slices=tuple(
            CompiledSlice(
                path=sl["path"],
                parts=tuple(sl["path"].split(".")[1:]),
                min_count=sl["min"],
                matchers=tuple(
                    SliceMatcher(
                        _split_sub_parts(sub),
                        kind,
                        exp,
                    )
                    for sub, (kind, exp) in sl["matchers"].items()
                ),
                max_count=_parse_max_count(sl.get("max")),
            )
            for sl in spec.get("slices", ())
        ),
        binding_specs=_compile_binding_specs(
            base_type,
            spec.get("binding_specs", {}),
            spec.get("bindings", {}),
        ),
        slice_groups=tuple(
            _compile_slice_group(sg, is_sub_group=False) for sg in spec.get("slice_groups", ())
        ),
        target_profiles=tuple(
            AllowedValuesRule(p, tuple(p.split(".")[1:]), frozenset(profiles))
            for p, profiles in spec.get("target_profiles", {}).items()
        ),
        target_aggregations=tuple(
            AllowedValuesRule(p, tuple(p.split(".")[1:]), frozenset(aggs))
            for p, aggs in spec.get("target_aggregations", {}).items()
        ),
        constraints=compile_constraints(spec.get("constraints", ())),
        preferred_bindings=_compile_preferred_bindings(
            base_type, spec.get("preferred_bindings", {})
        ),
        max_length=tuple(
            MaxLengthRule(p, tuple(p.split(".")[1:]), ml)
            for p, ml in spec.get("max_length", {}).items()
        ),
        value_bounds=_compile_value_bounds(
            spec.get("min_values", {}),
            spec.get("max_values", {}),
        ),
        element_profiles=tuple(
            AllowedValuesRule(p, tuple(p.split(".")[1:]), frozenset(profiles))
            for p, profiles in spec.get("element_profiles", {}).items()
        ),
        must_support=tuple(
            PathRule(p, tuple(p.split(".")[1:])) for p in spec.get("must_support", ())
        ),
    )


def compile_profiles(raw: dict[str, dict[str, Any]]) -> dict[str, CompiledProfile]:
    """Pre-compile raw StructureDefinition constraint dicts once at module load."""
    return {url: _compile_single_profile(spec) for url, spec in raw.items()}


COMPILED_PROFILES = compile_profiles(PROFILE_CONSTRAINTS)


def _check_required(
    resource: dict[str, Any], prof_url: str, rules: tuple[PathRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        if not rule.parts:
            continue
        parents = [resource] if len(rule.parts) == 1 else resolve_nodes(resource, rule.parts[:-1])
        if parents and not all(_check_child_present(p, rule.parts[-1]) for p in parents):
            issues.append(f"Profile[{prof_url}]: missing required element '{rule.path}'")
    return issues


def _check_forbidden_present(parent_val: Any, child_seg: str) -> bool:
    if not isinstance(parent_val, dict):
        return False
    if child_seg.endswith(_CHOICE_SUFFIX):
        stem = child_seg[:-_CHOICE_SUFFIX_LEN]
        return any(
            k.startswith(stem) and not k.startswith("_") and parent_val[k] is not None
            for k in parent_val
        )
    return child_seg in parent_val and parent_val[child_seg] is not None


def _check_forbidden(
    resource: dict[str, Any], prof_url: str, rules: tuple[PathRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        if not rule.parts:
            continue
        parents = [resource] if len(rule.parts) == 1 else resolve_nodes(resource, rule.parts[:-1])
        if any(_check_forbidden_present(p, rule.parts[-1]) for p in parents):
            issues.append(
                f"Profile[{prof_url}]: forbidden element '{rule.path}' (max=0) is present"
            )
    return issues


def _check_max_length(
    resource: dict[str, Any], prof_url: str, rules: tuple[MaxLengthRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        issues.extend(
            f"Profile[{prof_url}]: '{rule.path}' length {len(val)} "
            f"exceeds maxLength {rule.max_length}"
            for val in resolve_nodes(resource, rule.parts)
            if isinstance(val, str) and len(val) > rule.max_length
        )
    return issues


def _unwrap_comparable(val: Any) -> int | float | str | None:
    if isinstance(val, dict):
        val = val.get("value")
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float, str)):
        return val
    return None


def _compare_lt(a: int | float | str, b: int | float | str) -> bool:
    if isinstance(a, str) and isinstance(b, str):
        min_len = min(len(a), len(b))
        return a[:min_len] < b[:min_len]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a < b
    return False


def _check_single_bound(val: Any, rule: ValueBoundsRule, prof_url: str) -> list[str]:
    comp_val = _unwrap_comparable(val)
    if comp_val is None:
        return []
    issues: list[str] = []
    if rule.min_val is not None:
        comp_min = _unwrap_comparable(rule.min_val)
        if comp_min is not None and _compare_lt(comp_val, comp_min):
            issues.append(
                f"Profile[{prof_url}]: '{rule.path}' must be >= {rule.min_val!r}, got {val!r}"
            )
    if rule.max_val is not None:
        comp_max = _unwrap_comparable(rule.max_val)
        if comp_max is not None and _compare_lt(comp_max, comp_val):
            issues.append(
                f"Profile[{prof_url}]: '{rule.path}' must be <= {rule.max_val!r}, got {val!r}"
            )
    return issues


def _check_value_bounds(
    resource: dict[str, Any], prof_url: str, rules: tuple[ValueBoundsRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        for val in resolve_nodes(resource, rule.parts):
            issues.extend(_check_single_bound(val, rule, prof_url))
    return issues


def _check_element_profiles(
    resource: dict[str, Any],
    prof_url: str,
    rules: tuple[AllowedValuesRule, ...],
    ctx: _SliceEvalContext,
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        issues.extend(
            f"Profile[{prof_url}]: '{rule.path}' does not conform to "
            f"required profile(s) {sorted(rule.allowed)}"
            for val in resolve_nodes(resource, rule.parts)
            if isinstance(val, dict)
            and not any(_node_conforms_to_profile(val, p, ctx) for p in rule.allowed)
        )
    return issues


def _check_must_support(
    resource: dict[str, Any], prof_url: str, rules: tuple[PathRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        if not rule.parts:
            continue
        parents = [resource] if len(rule.parts) == 1 else resolve_nodes(resource, rule.parts[:-1])
        if parents and not all(_check_child_present(p, rule.parts[-1]) for p in parents):
            issues.append(f"Profile[{prof_url}]: mustSupport element '{rule.path}' is missing")
    return issues


def _check_max_one(
    resource: dict[str, Any], prof_url: str, rules: tuple[PathRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        if not rule.parts:
            continue
        parents = [resource] if len(rule.parts) == 1 else resolve_nodes(resource, rule.parts[:-1])
        leaf = rule.parts[-1]
        issues.extend(
            f"Profile[{prof_url}]: element '{rule.path}' exceeds max cardinality 1"
            for parent in parents
            if (
                isinstance(parent, dict)
                and isinstance(parent.get(leaf), list)
                and len(parent[leaf]) > 1
            )
        )
    return issues


def _check_fixed(
    resource: dict[str, Any], prof_url: str, rules: tuple[ValueRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        issues.extend(
            f"Profile[{prof_url}]: '{rule.path}' must equal fixed value {rule.expected!r}"
            for val in resolve_nodes(resource, rule.parts)
            if val != rule.expected
        )
    return issues


def _check_pattern(
    resource: dict[str, Any], prof_url: str, rules: tuple[ValueRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        issues.extend(
            f"Profile[{prof_url}]: '{rule.path}' does not match required pattern {rule.expected!r}"
            for val in resolve_nodes(resource, rule.parts)
            if not pattern_matches(val, rule.expected)
        )
    return issues


def _check_type_narrowing(
    resource: dict[str, Any], prof_url: str, rules: tuple[TypeNarrowingRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        parents = (
            [resource] if not rule.parent_parts else resolve_nodes(resource, rule.parent_parts)
        )
        for parent in parents:
            if not isinstance(parent, dict):
                continue
            for key, value in parent.items():
                if key.startswith(rule.stem) and not key.startswith("_") and value is not None:
                    suffix = key[len(rule.stem) :]
                    if suffix not in rule.allowed_suffixes:
                        issues.append(
                            f"Profile[{prof_url}]: '{rule.path}' narrowed to "
                            f"{rule.allowed_suffixes}, got '{key}'"
                        )
    return issues


def _check_single_ref_type(
    ref_obj: dict[str, Any], prof_url: str, rule: AllowedValuesRule
) -> list[str]:
    issues: list[str] = []
    raw_ref = ref_obj.get("reference")
    if isinstance(raw_ref, str):
        ref_rt = _extract_ref_resource_type(raw_ref)
        if ref_rt is not None and ref_rt not in rule.allowed:
            issues.append(
                f"Profile[{prof_url}]: '{rule.path}' reference target "
                f"'{ref_rt}' not in {sorted(rule.allowed)}"
            )
    raw_type = ref_obj.get("type")
    if isinstance(raw_type, str) and raw_type:
        explicit_rt = raw_type.rsplit("/", 1)[-1] if "/" in raw_type else raw_type
        if explicit_rt not in rule.allowed:
            issues.append(
                f"Profile[{prof_url}]: '{rule.path}' Reference.type "
                f"'{explicit_rt}' not in {sorted(rule.allowed)}"
            )
    return issues


def _check_target_types(
    resource: dict[str, Any], prof_url: str, rules: tuple[AllowedValuesRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        for ref_obj in resolve_nodes(resource, rule.parts):
            if isinstance(ref_obj, dict):
                issues.extend(_check_single_ref_type(ref_obj, prof_url, rule))
    return issues


def _check_bindings(
    resource: dict[str, Any],
    prof_url: str,
    rules: tuple[CompiledBindingRule, ...],
    tx_options: TxOptions,
    *,
    _warnings_out: list[str] | None = None,
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        for val in resolve_nodes(resource, rule.parts):
            res = validate_binding_value(
                val,
                rule.path,
                rule.value_set,
                rule.strength,
                tx_options,
                profile_prefix=f"Profile[{prof_url}]: ",
                vs_spec=rule.vs_spec,
                complete_systems=COMPLETE_CODE_SYSTEMS,
            )
            issues.extend(res.errors)
            if _warnings_out is not None and res.warnings:
                _warnings_out.extend(res.warnings)
    return issues


def _slice_item_matches(item: Any, matchers: tuple[SliceMatcher, ...]) -> bool:
    for matcher in matchers:
        sub_vals = [item] if not matcher.sub_parts else resolve_nodes(item, matcher.sub_parts)
        if matcher.kind == "fixed":
            if not any(v == matcher.expected for v in sub_vals):
                return False
        elif not any(pattern_matches(v, matcher.expected) for v in sub_vals):
            return False
    return True


def _check_slices(
    resource: dict[str, Any], prof_url: str, slices: tuple[CompiledSlice, ...]
) -> list[str]:
    issues: list[str] = []
    for sl in slices:
        items = resolve_nodes(resource, sl.parts)
        matches = sum(1 for item in items if _slice_item_matches(item, sl.matchers))
        if matches < sl.min_count:
            issues.append(
                f"Profile[{prof_url}]: slice at '{sl.path}' requires at least "
                f"{sl.min_count} matching item(s), found {matches}"
            )
        if sl.max_count is not None and matches > sl.max_count:
            issues.append(
                f"Profile[{prof_url}]: slice at '{sl.path}' allows at most "
                f"{sl.max_count} matching item(s), found {matches}"
            )
    return issues


@dataclass(frozen=True, slots=True)
class _SliceEvalContext:
    """Shared context for slice group matching and recursive profile validation."""

    root_resource: dict[str, Any]
    compiled_profiles: dict[str, CompiledProfile]
    tx_options: TxOptions
    bundle_index: dict[str, dict[str, Any]] | None
    visited_profiles: frozenset[str]
    visited_targets: frozenset[tuple[int, str]] = frozenset()


def _resolve_contained_reference(
    root_resource: dict[str, Any], target_id: str
) -> dict[str, Any] | None:
    contained = root_resource.get("contained")
    if not isinstance(contained, list):
        return None
    for res in contained:
        if isinstance(res, dict) and res.get("id") == target_id:
            return res
    return None


def _resolve_reference(
    node: Any,
    root_resource: dict[str, Any],
    bundle_index: dict[str, dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if isinstance(node, dict) and "resourceType" in node and "reference" not in node:
        return node
    ref = node.get("reference") if isinstance(node, dict) else node
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("#"):
        return _resolve_contained_reference(root_resource, ref[1:])
    if bundle_index is None:
        return None
    found = bundle_index.get(ref)
    if found is not None:
        return found
    rel_ref = extract_relative_ref(ref)
    return bundle_index.get(rel_ref) if rel_ref is not None else None


def _check_single_ref_aggregation(
    ref_obj: dict[str, Any], prof_url: str, rule: AllowedValuesRule, ctx: _SliceEvalContext
) -> str | None:
    ref = ref_obj.get("reference")
    if not isinstance(ref, str) or not ref:
        return None
    if ref.startswith("#"):
        return (
            None
            if "contained" in rule.allowed
            else f"Profile[{prof_url}]: '{rule.path}' reference '{ref}' uses "
            f"'contained' aggregation, allowed {sorted(rule.allowed)}"
        )
    if "referenced" in rule.allowed:
        return None
    if "bundled" not in rule.allowed:
        return (
            f"Profile[{prof_url}]: '{rule.path}' reference '{ref}' must be contained, "
            f"allowed {sorted(rule.allowed)}"
        )
    if (
        ctx.bundle_index is not None
        and _resolve_reference(ref_obj, ctx.root_resource, ctx.bundle_index) is not None
    ):
        return None
    return (
        f"Profile[{prof_url}]: '{rule.path}' reference '{ref}' must resolve in Bundle "
        "('bundled' aggregation)"
    )


def _check_target_aggregations(
    resource: dict[str, Any],
    prof_url: str,
    rules: tuple[AllowedValuesRule, ...],
    ctx: _SliceEvalContext,
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        for ref_obj in resolve_nodes(resource, rule.parts):
            if isinstance(ref_obj, dict):
                err = _check_single_ref_aggregation(ref_obj, prof_url, rule, ctx)
                if err is not None:
                    issues.append(err)
    return issues


def _target_conforms_to_profile(
    target: dict[str, Any], tp_url: str, ctx: _SliceEvalContext
) -> bool:
    tp_key = tp_url.split("|", 1)[0].strip()
    key = (id(target), tp_key)
    if key in ctx.visited_targets:
        return True
    spec_p = ctx.compiled_profiles.get(tp_key)
    if spec_p is None:
        if tp_key.startswith("http://hl7.org/fhir/StructureDefinition/"):
            expected = tp_key.rsplit("/", 1)[-1]
            if expected in ("Resource", "DomainResource"):
                return True
            actual_rt = target.get("resourceType")
            return actual_rt == expected
        return True
    target_rtype = target.get("resourceType") or spec_p.base_type
    if not isinstance(target_rtype, str) or not target_rtype:
        return False
    issues = validate_single_profile(
        target,
        target_rtype,
        tp_key,
        compiled_profiles=ctx.compiled_profiles,
        tx=ctx.tx_options,
        bundle_index=ctx.bundle_index,
        _visited_profiles=frozenset({tp_key}),
        _visited_targets=ctx.visited_targets | {key},
    )
    return not issues


def _check_target_profiles(
    resource: dict[str, Any],
    prof_url: str,
    rules: tuple[AllowedValuesRule, ...],
    ctx: _SliceEvalContext,
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        for ref_obj in resolve_nodes(resource, rule.parts):
            if not isinstance(ref_obj, dict):
                continue
            target = _resolve_reference(ref_obj, ctx.root_resource, ctx.bundle_index)
            if target is None:
                continue
            if not any(_target_conforms_to_profile(target, tp, ctx) for tp in sorted(rule.allowed)):
                issues.append(
                    f"Profile[{prof_url}]: '{rule.path}' target does not conform to any "
                    f"targetProfile in {sorted(rule.allowed)}"
                )
    return issues


_PY_TO_FHIR_TYPE: dict[type[Any], str] = {
    bool: "boolean",
    int: "integer",
    float: "decimal",
    str: "string",
}


def _infer_node_type(val: Any, inferred_type: str | None) -> str | None:
    if inferred_type is not None:
        return inferred_type
    if isinstance(val, dict) and isinstance(val.get("resourceType"), str):
        return str(val["resourceType"])
    return _PY_TO_FHIR_TYPE.get(type(val))


def _type_matches(val: Any, inferred_type: str | None, allowed: tuple[str, ...]) -> bool:
    if inferred_type is not None:
        return inferred_type in allowed or (inferred_type == "integer" and "decimal" in allowed)
    if isinstance(val, dict):
        rt = val.get("resourceType")
        if isinstance(rt, str):
            return rt in allowed
        return any(t not in RESOURCE_MODELS and t not in _FHIR_PRIMITIVES for t in allowed)
    if isinstance(val, bool):
        return "boolean" in allowed
    if isinstance(val, int):
        return any(t in _INT_FHIR_TYPES for t in allowed)
    return (isinstance(val, float) and "decimal" in allowed) or (
        isinstance(val, str) and any(t in _STR_FHIR_TYPES for t in allowed)
    )


def _node_conforms_to_profile(
    target: dict[str, Any], prof_url: str, ctx: _SliceEvalContext
) -> bool:
    if prof_url in ctx.visited_profiles:
        return True
    spec_p = ctx.compiled_profiles.get(prof_url)
    if spec_p is None:
        if prof_url.startswith("http://hl7.org/fhir/StructureDefinition/"):
            expected = prof_url.rsplit("/", 1)[-1]
            actual_rt = target.get("resourceType")
            return not isinstance(actual_rt, str) or actual_rt == expected
        return True
    target_rtype = target.get("resourceType") or spec_p.base_type
    if not isinstance(target_rtype, str) or not target_rtype:
        return False
    issues = validate_single_profile(
        target,
        target_rtype,
        prof_url,
        compiled_profiles=ctx.compiled_profiles,
        tx=ctx.tx_options,
        bundle_index=ctx.bundle_index,
        _visited_profiles=ctx.visited_profiles | {prof_url},
    )
    return not issues


def _find_constraint(
    constraints: tuple[tuple[tuple[str, ...], Any], ...],
    sub_parts: tuple[str, ...],
) -> Any | None:
    for parts, value in constraints:
        if parts == sub_parts:
            return value
    return None


def _match_value_or_pattern_disc(
    item: Any, sl: CompiledSliceRule, disc: SliceDiscriminator, ctx: _SliceEvalContext
) -> bool:
    exact = [m for m in sl.matchers if m.sub_parts == disc.sub_parts]
    if not exact:
        prefix_len = len(disc.sub_parts)
        nested = [
            m
            for m in sl.matchers
            if len(m.sub_parts) > prefix_len and m.sub_parts[:prefix_len] == disc.sub_parts
        ]
        return _slice_item_matches(item, tuple(nested)) if nested else False

    nodes = [item] if not disc.sub_parts else resolve_nodes(item, disc.sub_parts)
    if disc.resolve_target:
        nodes = [
            res
            for n in nodes
            if (res := _resolve_reference(n, ctx.root_resource, ctx.bundle_index)) is not None
        ]
    for m in exact:
        prefer_fixed = (disc.kind == "value" and m.kind == "fixed") or (
            disc.kind == "pattern" and m.kind != "pattern"
        )
        matched = (
            any(v == m.expected for v in nodes)
            if prefer_fixed
            else any(pattern_matches(v, m.expected) for v in nodes)
        )
        if not matched:
            return False
    return True


def _eval_type_constraint(
    item: Any,
    inferred_type: str | None,
    sub_parts: tuple[str, ...],
    allowed: tuple[str, ...],
) -> bool:
    if not sub_parts:
        return _type_matches(item, inferred_type, allowed)
    typed_nodes = resolve_typed_nodes(item, sub_parts)
    return any(_type_matches(v, inf, allowed) for v, inf in typed_nodes)


def _eval_profile_constraint(
    item: Any,
    sub_parts: tuple[str, ...],
    req_profiles: tuple[str, ...],
    ctx: _SliceEvalContext,
    *,
    resolve_target: bool = False,
) -> bool:
    raw_nodes = [item] if not sub_parts else resolve_nodes(item, sub_parts)
    if resolve_target:
        targets = [
            res
            for n in raw_nodes
            if (res := _resolve_reference(n, ctx.root_resource, ctx.bundle_index)) is not None
        ]
    else:
        targets = [n for n in raw_nodes if isinstance(n, dict)]
    return any(all(_node_conforms_to_profile(t, p, ctx) for p in req_profiles) for t in targets)


def _eval_exists_constraint(
    item: Any,
    sub_parts: tuple[str, ...],
    expected: bool,
) -> bool:
    nodes = [item] if not sub_parts else resolve_nodes(item, sub_parts)
    return any(v is not None for v in nodes) is bool(expected)


def _match_type_disc(
    item: Any,
    inferred_type: str | None,
    sl: CompiledSliceRule,
    disc: SliceDiscriminator,
    ctx: _SliceEvalContext,
) -> bool:
    allowed: tuple[str, ...] | None = _find_constraint(sl.type_constraints, disc.sub_parts)
    if not allowed:
        return False
    if not disc.resolve_target:
        return _eval_type_constraint(item, inferred_type, disc.sub_parts, allowed)
    typed_nodes = (
        [(item, inferred_type)] if not disc.sub_parts else resolve_typed_nodes(item, disc.sub_parts)
    )
    resolved = [_resolve_reference(v, ctx.root_resource, ctx.bundle_index) for v, _ in typed_nodes]
    return any(_type_matches(r, None, allowed) for r in resolved if r is not None)


def _match_profile_disc(
    item: Any, sl: CompiledSliceRule, disc: SliceDiscriminator, ctx: _SliceEvalContext
) -> bool:
    req_profiles: tuple[str, ...] | None = _find_constraint(sl.profile_constraints, disc.sub_parts)
    if not req_profiles:
        return False
    return _eval_profile_constraint(
        item, disc.sub_parts, req_profiles, ctx, resolve_target=disc.resolve_target
    )


def _match_exists_disc(item: Any, sl: CompiledSliceRule, disc: SliceDiscriminator) -> bool:
    expected = _find_constraint(sl.exists_constraints, disc.sub_parts)
    if expected is None:
        return False
    return _eval_exists_constraint(item, disc.sub_parts, expected)


def _item_matches_discriminator(
    item: Any,
    inferred_type: str | None,
    sl: CompiledSliceRule,
    disc: SliceDiscriminator,
    ctx: _SliceEvalContext,
) -> bool:
    if disc.kind in {"value", "pattern"}:
        return _match_value_or_pattern_disc(item, sl, disc, ctx)
    if disc.kind == "type":
        return _match_type_disc(item, inferred_type, sl, disc, ctx)
    if disc.kind == "profile":
        return _match_profile_disc(item, sl, disc, ctx)
    if disc.kind == "exists":
        return _match_exists_disc(item, sl, disc)
    return False


def _slice_constraints_satisfied(
    item: Any,
    inferred_type: str | None,
    sl: CompiledSliceRule,
    ctx: _SliceEvalContext,
    skip_resolved: frozenset[tuple[str, tuple[str, ...]]] = frozenset(),
) -> bool:
    resolved_val_parts = {sp for kind, sp in skip_resolved if kind in {"value", "pattern"}}
    active_matchers = (
        tuple(m for m in sl.matchers if m.sub_parts not in resolved_val_parts)
        if resolved_val_parts
        else sl.matchers
    )
    if active_matchers and not _slice_item_matches(item, active_matchers):
        return False
    if not all(
        _eval_type_constraint(item, inferred_type, sp, allowed)
        for sp, allowed in sl.type_constraints
        if ("type", sp) not in skip_resolved
    ):
        return False
    if not all(
        _eval_profile_constraint(item, sp, req_profiles, ctx)
        for sp, req_profiles in sl.profile_constraints
        if ("profile", sp) not in skip_resolved
    ):
        return False
    return all(
        _eval_exists_constraint(item, sp, expected)
        for sp, expected in sl.exists_constraints
        if ("exists", sp) not in skip_resolved
    )


def _item_matches_no_disc(
    item: Any,
    inferred_type: str | None,
    sl: CompiledSliceRule,
    ctx: _SliceEvalContext,
) -> bool:
    has_any = sl.matchers or sl.type_constraints or sl.profile_constraints or sl.exists_constraints
    if not has_any:
        return False
    return _slice_constraints_satisfied(item, inferred_type, sl, ctx)


def _item_matches_slice(
    item: Any,
    inferred_type: str | None,
    sl: CompiledSliceRule,
    discriminators: tuple[SliceDiscriminator, ...],
    ctx: _SliceEvalContext,
) -> bool:
    if not discriminators:
        return _item_matches_no_disc(item, inferred_type, sl, ctx)
    return all(
        _item_matches_discriminator(item, inferred_type, sl, disc, ctx) for disc in discriminators
    )


def _check_group_ordering_and_rules(
    group: CompiledSliceGroup,
    prof_url: str,
    unmatched_indices: list[int],
    matched_seq: list[tuple[int, int]],
) -> list[str]:
    issues: list[str] = []
    if group.rules == "closed" and unmatched_indices:
        issues.append(
            f"Profile[{prof_url}]: closed slice at '{group.path}' found "
            f"{len(unmatched_indices)} unmatched item(s)"
        )
    elif group.rules == "openAtEnd" and unmatched_indices and matched_seq:
        last_matched_idx = max(item_idx for item_idx, _ in matched_seq)
        if any(u_idx < last_matched_idx for u_idx in unmatched_indices):
            issues.append(
                f"Profile[{prof_url}]: openAtEnd slice at '{group.path}' "
                "has unmatched item before the end"
            )
    if group.ordered and len(matched_seq) > 1:
        slice_order = [s_idx for _, s_idx in matched_seq]
        if any(b < a for a, b in pairwise(slice_order)):
            issues.append(
                f"Profile[{prof_url}]: ordered slice at '{group.path}' has items out of order"
            )
    return issues


def _check_single_slice_group(
    target: dict[str, Any],
    prof_url: str,
    group: CompiledSliceGroup,
    ctx: _SliceEvalContext,
) -> list[str]:
    items = resolve_typed_nodes(target, group.parts)
    matched_by_slice: list[list[tuple[Any, str | None]]] = [[] for _ in group.slices]
    unmatched_indices: list[int] = []
    matched_seq: list[tuple[int, int]] = []

    for item_idx, (item, inferred_type) in enumerate(items):
        hit_indices = [
            s_idx
            for s_idx, sl in enumerate(group.slices)
            if _item_matches_slice(item, inferred_type, sl, group.discriminators, ctx)
        ]
        if not hit_indices:
            unmatched_indices.append(item_idx)
            continue
        for s_idx in hit_indices:
            matched_by_slice[s_idx].append((item, inferred_type))
        matched_seq.append((item_idx, hit_indices[0]))

    skip_resolved = frozenset(
        (d.kind, d.sub_parts) for d in group.discriminators if d.resolve_target
    )
    issues = _check_group_ordering_and_rules(group, prof_url, unmatched_indices, matched_seq)
    for s_idx, sl in enumerate(group.slices):
        matched_items = matched_by_slice[s_idx]
        count = len(matched_items)
        if count < sl.min_count:
            issues.append(
                f"Profile[{prof_url}]: slice at '{group.path}' requires at least "
                f"{sl.min_count} matching item(s), found {count}"
            )
        if sl.max_count is not None and count > sl.max_count:
            issues.append(
                f"Profile[{prof_url}]: slice at '{group.path}' allows at most "
                f"{sl.max_count} matching item(s), found {count}"
            )
        for matched_item, inferred_type in matched_items:
            if not _slice_constraints_satisfied(
                matched_item, inferred_type, sl, ctx, skip_resolved
            ):
                issues.append(
                    f"Profile[{prof_url}]: item in slice '{group.path}:{sl.slice_name}' "
                    "does not satisfy slice constraints"
                )
            if sl.sub_groups and isinstance(matched_item, dict):
                issues.extend(_check_slice_groups(matched_item, prof_url, sl.sub_groups, ctx))
    return issues


def _check_slice_groups(
    target: dict[str, Any],
    prof_url: str,
    slice_groups: tuple[CompiledSliceGroup, ...],
    ctx: _SliceEvalContext,
) -> list[str]:
    issues: list[str] = []
    for group in slice_groups:
        issues.extend(_check_single_slice_group(target, prof_url, group, ctx))
    return issues


def _has_first_segment(resource: dict[str, Any], seg: str) -> bool:
    if not seg.endswith(_CHOICE_SUFFIX):
        return seg in resource
    stem = seg[:-_CHOICE_SUFFIX_LEN]
    stem_len = len(stem)
    return any(k.startswith(stem) and len(k) > stem_len and k[stem_len].isupper() for k in resource)


def check_constraints(
    resource: dict[str, Any],
    constraints: tuple[CompiledConstraint, ...],
    *,
    bundle_index: dict[str, dict[str, Any]] | None = None,
    warnings_out: list[str] | None = None,
) -> list[str]:
    """Evaluate pre-compiled FHIRPath constraints with O(1) field short-circuits."""
    if not constraints:
        return []
    issues: list[str] = []
    ctx = EvalContext(resource=resource, root_resource=resource, bundle_index=bundle_index)
    for c in constraints:
        if c.requires_contained and "contained" not in resource:
            continue
        if c.parts and not _has_first_segment(resource, c.parts[0]):
            continue
        nodes = [resource] if not c.parts else resolve_nodes(resource, c.parts)
        for node in nodes:
            if not evaluate_compiled_invariant(c.evaluator, node, ctx):
                if c.severity == "error":
                    issues.append(f"Invariant[{c.key}] {c.path}: {c.human}")
                elif c.severity == "warning" and warnings_out is not None:
                    warnings_out.append(f"Warning: Invariant[{c.key}] {c.path}: {c.human}")
                break
    return issues


def validate_single_profile(
    resource: dict[str, Any],
    rtype: str,
    prof_url: str,
    compiled_profiles: dict[str, CompiledProfile] = COMPILED_PROFILES,
    **kwargs: Any,
) -> list[str]:
    """Validate a resource against a single compiled IG StructureDefinition constraint set."""
    compiled_map: dict[str, CompiledProfile] | None = kwargs.get("compiled_map")
    effective_profiles = compiled_map if compiled_map is not None else compiled_profiles
    spec = effective_profiles.get(prof_url)
    if spec is None:
        return []

    if spec.base_type and spec.base_type != rtype:
        return [f"Profile[{prof_url}]: profile applies to '{spec.base_type}', got '{rtype}'"]

    tx_raw = kwargs.get("tx", "local")
    strict_extensible = bool(kwargs.get("strict_extensible", False))
    best_practice = bool(kwargs.get("best_practice", False))
    enforce_must_support = bool(kwargs.get("enforce_must_support", False))
    _warnings_out: list[str] | None = kwargs.get("_warnings_out")
    tx_options = (
        tx_raw
        if isinstance(tx_raw, TxOptions)
        else parse_tx_options(tx_raw, strict_extensible=strict_extensible)
    )
    bundle_index: dict[str, dict[str, Any]] | None = kwargs.get("bundle_index")
    visited_profiles: frozenset[str] = kwargs.get("_visited_profiles", frozenset({prof_url}))
    visited_targets: frozenset[tuple[int, str]] = kwargs.get("_visited_targets", frozenset()) | {
        (id(resource), prof_url)
    }

    ctx = _SliceEvalContext(
        root_resource=resource,
        compiled_profiles=effective_profiles,
        tx_options=tx_options,
        bundle_index=bundle_index,
        visited_profiles=visited_profiles,
        visited_targets=visited_targets,
    )
    slice_issues = (
        _check_slice_groups(resource, prof_url, spec.slice_groups, ctx)
        if spec.slice_groups
        else _check_slices(resource, prof_url, spec.slices)
    )

    if best_practice and _warnings_out is not None and tx_options.mode != "off":
        _check_bindings(
            resource,
            prof_url,
            spec.preferred_bindings,
            tx_options,
            _warnings_out=_warnings_out,
        )

    issues = [
        *_check_required(resource, prof_url, spec.required),
        *_check_forbidden(resource, prof_url, spec.forbidden),
        *_check_max_one(resource, prof_url, spec.max_one),
        *_check_fixed(resource, prof_url, spec.fixed),
        *_check_pattern(resource, prof_url, spec.pattern),
        *_check_type_narrowing(resource, prof_url, spec.type_narrowing),
        *_check_target_types(resource, prof_url, spec.target_types),
        *_check_target_aggregations(resource, prof_url, spec.target_aggregations, ctx),
        *_check_target_profiles(resource, prof_url, spec.target_profiles, ctx),
        *_check_bindings(
            resource,
            prof_url,
            spec.binding_specs,
            tx_options,
            _warnings_out=_warnings_out,
        ),
        *check_constraints(
            resource,
            spec.constraints,
            bundle_index=bundle_index,
            warnings_out=_warnings_out,
        ),
        *slice_issues,
    ]
    if spec.max_length:
        issues.extend(_check_max_length(resource, prof_url, spec.max_length))
    if spec.value_bounds:
        issues.extend(_check_value_bounds(resource, prof_url, spec.value_bounds))
    if spec.element_profiles:
        issues.extend(_check_element_profiles(resource, prof_url, spec.element_profiles, ctx))
    if enforce_must_support and spec.must_support:
        issues.extend(_check_must_support(resource, prof_url, spec.must_support))
    return issues
