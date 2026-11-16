"""Semantic validation for FHIR R4 Questionnaire and QuestionnaireResponse."""

from __future__ import annotations

import operator as _op
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, TypeGuard

from fhirlance.profiles import VALUE_SET_SPECS
from fhirlance.terminology import TxOptions, validate_binding_value

_MAX_ITEM_DEPTH = 64

_ENABLE_WHEN_ANSWER_KEYS: dict[str, frozenset[str]] = {
    "boolean": frozenset({"answerBoolean"}),
    "integer": frozenset({"answerInteger"}),
    "decimal": frozenset({"answerDecimal", "answerInteger"}),
    "date": frozenset({"answerDate"}),
    "dateTime": frozenset({"answerDateTime"}),
    "time": frozenset({"answerTime"}),
    "string": frozenset({"answerString"}),
    "text": frozenset({"answerString"}),
    "url": frozenset({"answerString"}),
    "choice": frozenset(
        {"answerCoding", "answerString", "answerDate", "answerTime", "answerInteger"}
    ),
    "open-choice": frozenset(
        {"answerCoding", "answerString", "answerDate", "answerTime", "answerInteger"}
    ),
    "quantity": frozenset({"answerQuantity"}),
    "reference": frozenset({"answerReference"}),
    "group": frozenset(),
    "display": frozenset(),
}

_RESPONSE_VALUE_KEYS: dict[str, frozenset[str]] = {
    "boolean": frozenset({"valueBoolean"}),
    "integer": frozenset({"valueInteger"}),
    "decimal": frozenset({"valueDecimal", "valueInteger"}),
    "date": frozenset({"valueDate"}),
    "dateTime": frozenset({"valueDateTime"}),
    "time": frozenset({"valueTime"}),
    "string": frozenset({"valueString"}),
    "text": frozenset({"valueString"}),
    "url": frozenset({"valueUri", "valueString"}),
    "choice": frozenset({"valueCoding", "valueString", "valueDate", "valueTime", "valueInteger"}),
    "open-choice": frozenset(
        {"valueCoding", "valueString", "valueDate", "valueTime", "valueInteger"}
    ),
    "attachment": frozenset({"valueAttachment"}),
    "quantity": frozenset({"valueQuantity"}),
    "reference": frozenset({"valueReference"}),
    "group": frozenset(),
    "display": frozenset(),
}


@dataclass(frozen=True, slots=True)
class _QuestionnaireIndex:
    items_by_link_id: dict[str, dict[str, Any]]
    root_items: list[dict[str, Any]]


@dataclass(frozen=True, slots=True)
class _QuestionnaireValidationCtx:
    index: _QuestionnaireIndex
    tx_options: TxOptions | None
    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True, slots=True)
class _ResponseValidationCtx:
    q_index: _QuestionnaireIndex
    tx_options: TxOptions | None
    errors: list[str]


def _strip_canonical_version(canonical: str) -> str:
    return canonical.split("|", 1)[0]


def _index_questionnaire_items(
    items: Any,
    items_by_link_id: dict[str, dict[str, Any]],
    depth: int = 0,
) -> None:
    if not isinstance(items, list) or depth > _MAX_ITEM_DEPTH:
        return
    for item in items:
        if not isinstance(item, dict):
            continue
        link_id = item.get("linkId")
        if isinstance(link_id, str) and link_id:
            items_by_link_id[link_id] = item
        _index_questionnaire_items(item.get("item"), items_by_link_id, depth + 1)


def _build_questionnaire_index(questionnaire: dict[str, Any]) -> _QuestionnaireIndex:
    items_by_link_id: dict[str, dict[str, Any]] = {}
    raw_items = questionnaire.get("item")
    root_items = (
        [i for i in raw_items if isinstance(i, dict)] if isinstance(raw_items, list) else []
    )
    _index_questionnaire_items(root_items, items_by_link_id)
    return _QuestionnaireIndex(items_by_link_id=items_by_link_id, root_items=root_items)


def _validate_enable_when_entry(
    cond: dict[str, Any],
    path: str,
    items_by_link_id: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    question_id = cond.get("question")
    if not isinstance(question_id, str) or not question_id:
        return
    target = items_by_link_id.get(question_id)
    if target is None:
        errors.append(
            f"{path}: enableWhen.question '{question_id}' does not reference a linkId "
            "in Questionnaire"
        )
        return

    if cond.get("operator") == "exists":
        return

    target_type = target.get("type")
    if not isinstance(target_type, str):
        return
    allowed = _ENABLE_WHEN_ANSWER_KEYS.get(target_type)
    if allowed is None:
        return

    errors.extend(
        f"{path}: enableWhen answer key '{ans_key}' is incompatible with "
        f"question '{question_id}' type '{target_type}'"
        for ans_key in cond
        if ans_key.startswith("answer") and ans_key not in allowed
    )


def _validate_questionnaire_items(
    items: Any,
    path: str,
    ctx: _QuestionnaireValidationCtx,
    depth: int = 0,
) -> None:
    if not isinstance(items, list) or depth > _MAX_ITEM_DEPTH:
        return

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_path = f"{path}.item[{idx}]"
        enable_when = item.get("enableWhen")
        if isinstance(enable_when, list):
            for ew_idx, cond in enumerate(enable_when):
                if isinstance(cond, dict):
                    _validate_enable_when_entry(
                        cond,
                        f"{item_path}.enableWhen[{ew_idx}]",
                        ctx.index.items_by_link_id,
                        ctx.errors,
                    )

        answer_vs = item.get("answerValueSet")
        if (
            ctx.tx_options is not None
            and ctx.tx_options.mode != "off"
            and isinstance(answer_vs, str)
            and answer_vs
        ):
            canonical = _strip_canonical_version(answer_vs)
            if canonical not in VALUE_SET_SPECS:
                ctx.warnings.append(
                    f"{item_path}.answerValueSet: ValueSet '{answer_vs}' is not in "
                    "known VALUE_SET_SPECS"
                )

        _validate_questionnaire_items(item.get("item"), item_path, ctx, depth + 1)


def validate_questionnaire_semantics(
    resource: dict[str, Any],
    tx_options: TxOptions | None = None,
    warnings_out: list[str] | None = None,
) -> list[str]:
    """Validate semantic constraints on a FHIR R4 Questionnaire resource."""
    errors: list[str] = []
    warnings: list[str] = []
    index = _build_questionnaire_index(resource)
    ctx = _QuestionnaireValidationCtx(
        index=index,
        tx_options=tx_options,
        errors=errors,
        warnings=warnings,
    )
    _validate_questionnaire_items(index.root_items, "Questionnaire", ctx)
    if warnings_out is not None and warnings:
        warnings_out.extend(warnings)
    return errors


def _codings_match(actual: dict[str, Any], expected: dict[str, Any]) -> bool:
    actual_code = actual.get("code")
    expected_code = expected.get("code")
    if actual_code is None or expected_code is None or actual_code != expected_code:
        return False
    actual_sys = actual.get("system")
    expected_sys = expected.get("system")
    if actual_sys and expected_sys:
        return bool(actual_sys == expected_sys)
    return True


def _answer_matches_option(val_key: str, val: Any, options: list[Any]) -> bool:
    for opt in options:
        if not isinstance(opt, dict) or val_key not in opt:
            continue
        opt_val = opt[val_key]
        if val_key == "valueCoding" and isinstance(val, dict) and isinstance(opt_val, dict):
            if _codings_match(val, opt_val):
                return True
        elif opt_val == val:
            return True
    return False


def _validate_response_answer(
    ans: dict[str, Any],
    ans_path: str,
    q_item: dict[str, Any],
    ctx: _ResponseValidationCtx,
) -> None:
    q_type = q_item.get("type")
    value_keys = [k for k in ans if k.startswith("value")]
    answer_options = q_item.get("answerOption")
    has_options = isinstance(answer_options, list) and len(answer_options) > 0
    raw_vs = q_item.get("answerValueSet")

    for val_key in value_keys:
        if isinstance(q_type, str):
            allowed = _RESPONSE_VALUE_KEYS.get(q_type)
            if allowed is not None and val_key not in allowed:
                ctx.errors.append(
                    f"{ans_path}.{val_key}: value type '{val_key}' is incompatible with "
                    f"Questionnaire item type '{q_type}'"
                )

        if (
            has_options
            and q_type != "open-choice"
            and isinstance(answer_options, list)
            and not _answer_matches_option(val_key, ans[val_key], answer_options)
        ):
            ctx.errors.append(
                f"{ans_path}.{val_key}: value does not match any allowed answerOption"
            )

        if (
            ctx.tx_options is not None
            and ctx.tx_options.mode != "off"
            and q_type != "open-choice"
            and isinstance(raw_vs, str)
            and raw_vs
            and val_key in ("valueCoding", "valueString")
        ):
            vs_url = _strip_canonical_version(raw_vs)
            if vs_url in VALUE_SET_SPECS:
                res = validate_binding_value(
                    ans[val_key],
                    f"{ans_path}.{val_key}",
                    vs_url,
                    "required",
                    ctx.tx_options,
                    vs_spec=VALUE_SET_SPECS[vs_url],
                )
                ctx.errors.extend(res.errors)


def _validate_response_items(
    items: Any,
    path: str,
    ctx: _ResponseValidationCtx,
    depth: int = 0,
) -> None:
    if not isinstance(items, list) or depth > _MAX_ITEM_DEPTH:
        return

    for idx, r_item in enumerate(items):
        if not isinstance(r_item, dict):
            continue
        item_path = f"{path}.item[{idx}]"
        link_id = r_item.get("linkId")
        q_item = ctx.q_index.items_by_link_id.get(link_id) if isinstance(link_id, str) else None

        if ctx.q_index.items_by_link_id and isinstance(link_id, str) and q_item is None:
            ctx.errors.append(f"{item_path}: linkId '{link_id}' does not exist in Questionnaire")

        raw_answers = r_item.get("answer")
        answers = (
            [a for a in raw_answers if isinstance(a, dict)] if isinstance(raw_answers, list) else []
        )

        if q_item is not None and not q_item.get("repeats") and len(answers) > 1:
            ctx.errors.append(
                f"{item_path}: item '{link_id}' does not allow repeating answers "
                f"(got {len(answers)})"
            )

        for ans_idx, ans in enumerate(answers):
            ans_path = f"{item_path}.answer[{ans_idx}]"
            if q_item is not None:
                _validate_response_answer(ans, ans_path, q_item, ctx)
            _validate_response_items(ans.get("item"), ans_path, ctx, depth + 1)

        _validate_response_items(r_item.get("item"), item_path, ctx, depth + 1)


def _collect_answered_map(
    items: Any,
    answered: dict[str, list[dict[str, Any]]],
    depth: int = 0,
) -> None:
    if not isinstance(items, list) or depth > _MAX_ITEM_DEPTH:
        return
    for r_item in items:
        if not isinstance(r_item, dict):
            continue
        link_id = r_item.get("linkId")
        raw_answers = r_item.get("answer")
        if isinstance(link_id, str) and isinstance(raw_answers, list):
            ans_dicts = [a for a in raw_answers if isinstance(a, dict)]
            if ans_dicts:
                answered.setdefault(link_id, []).extend(ans_dicts)
            for ans in ans_dicts:
                _collect_answered_map(ans.get("item"), answered, depth + 1)
        _collect_answered_map(r_item.get("item"), answered, depth + 1)


def _extract_first_prefixed_value(mapping: dict[str, Any], prefix: str) -> Any:
    for key, val in mapping.items():
        if key.startswith(prefix):
            return val
    return None


def _is_number(val: Any) -> TypeGuard[int | float]:
    return isinstance(val, (int, float)) and not isinstance(val, bool)


def _values_equal(actual: Any, expected: Any) -> bool:
    if isinstance(actual, bool) != isinstance(expected, bool):
        return False
    if isinstance(actual, dict) and isinstance(expected, dict):
        if "code" in actual or "code" in expected:
            return _codings_match(actual, expected)
        if "value" in actual and "value" in expected:
            return _values_equal(actual.get("value"), expected.get("value"))
    if _is_number(actual) and _is_number(expected):
        return bool(float(actual) == float(expected))
    return bool(actual == expected)


_ORDINAL_OPS: dict[str, Callable[[Any, Any], bool]] = {
    ">": _op.gt,
    "<": _op.lt,
    ">=": _op.ge,
    "<=": _op.le,
}


def _compare_ordinal(actual: Any, expected: Any, cmp_fn: Callable[[Any, Any], bool]) -> bool:
    if _is_number(actual) and _is_number(expected):
        return cmp_fn(float(actual), float(expected))
    if isinstance(actual, str) and isinstance(expected, str):
        return cmp_fn(actual, expected)
    if isinstance(actual, dict) and isinstance(expected, dict):
        actual_val = actual.get("value")
        expected_val = expected.get("value")
        if _is_number(actual_val) and _is_number(expected_val):
            return cmp_fn(float(actual_val), float(expected_val))
    return False


def _compare_values(actual: Any, expected: Any, op_name: str) -> bool:
    if op_name == "=":
        return _values_equal(actual, expected)
    if op_name == "!=":
        return not _values_equal(actual, expected)
    cmp_fn = _ORDINAL_OPS.get(op_name)
    if cmp_fn is None:
        return False
    return _compare_ordinal(actual, expected, cmp_fn)


def _eval_enable_when_cond(
    cond: dict[str, Any],
    answered: dict[str, list[dict[str, Any]]],
) -> bool:
    q_id = cond.get("question")
    if not isinstance(q_id, str):
        return False
    operator = cond.get("operator", "=")
    ans_list = answered.get(q_id, [])

    if operator == "exists":
        expected_exists = cond.get("answerBoolean")
        has_ans = len(ans_list) > 0
        return (not has_ans) if expected_exists is False else has_ans

    if not ans_list or not isinstance(operator, str):
        return False

    expected_val = _extract_first_prefixed_value(cond, "answer")
    for ans in ans_list:
        actual_val = _extract_first_prefixed_value(ans, "value")
        if actual_val is not None and _compare_values(actual_val, expected_val, operator):
            return True
    return False


def _is_item_enabled(
    q_item: dict[str, Any],
    answered: dict[str, list[dict[str, Any]]],
) -> bool:
    enable_when = q_item.get("enableWhen")
    if not isinstance(enable_when, list) or not enable_when:
        return True
    conds = [c for c in enable_when if isinstance(c, dict)]
    if not conds:
        return True
    if q_item.get("enableBehavior") == "any":
        return any(_eval_enable_when_cond(c, answered) for c in conds)
    return all(_eval_enable_when_cond(c, answered) for c in conds)


def _check_required_items(
    items: Any,
    answered: dict[str, list[dict[str, Any]]],
    errors: list[str],
    depth: int = 0,
) -> None:
    if not isinstance(items, list) or depth > _MAX_ITEM_DEPTH:
        return
    for q_item in items:
        if not isinstance(q_item, dict):
            continue
        if not _is_item_enabled(q_item, answered):
            continue
        link_id = q_item.get("linkId")
        q_type = q_item.get("type")
        if (
            q_item.get("required") is True
            and q_type not in ("group", "display")
            and isinstance(link_id, str)
            and not answered.get(link_id)
        ):
            errors.append(
                f"QuestionnaireResponse: required Questionnaire item '{link_id}' is missing"
            )
        _check_required_items(q_item.get("item"), answered, errors, depth + 1)


def validate_questionnaire_response_against_questionnaire(
    response: dict[str, Any],
    questionnaire: dict[str, Any],
    tx_options: TxOptions | None = None,
) -> list[str]:
    """Validate a QuestionnaireResponse against its referenced Questionnaire."""
    errors: list[str] = []
    q_index = _build_questionnaire_index(questionnaire)
    ctx = _ResponseValidationCtx(q_index=q_index, tx_options=tx_options, errors=errors)

    _validate_response_items(response.get("item"), "QuestionnaireResponse", ctx)

    answered: dict[str, list[dict[str, Any]]] = {}
    _collect_answered_map(response.get("item"), answered)
    _check_required_items(q_index.root_items, answered, errors)
    return errors
