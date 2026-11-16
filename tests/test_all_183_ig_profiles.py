"""Exhaustive test suite covering all 183 compiled IG profiles and 2,000+ profile constraints."""

from __future__ import annotations

from typing import Any

import pytest

from fhirlance import PROFILE_CONSTRAINTS, RESOURCE_MODELS
from fhirlance import types as fhir_types
from fhirlance.profile_engine import (
    COMPILED_PROFILES,
    AllowedValuesRule,
    CompiledProfile,
    CompiledSlice,
    PathRule,
    TypeNarrowingRule,
    ValueRule,
    _check_slices,
    validate_single_profile,
)


def _profile_short_id(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def _build_node_with_path(
    parts: tuple[str, ...],
    leaf_val: Any,
    *,
    keep_choice_leaf: bool = False,
) -> dict[str, Any]:
    if not parts:
        return {}
    head = parts[0]
    if len(parts) == 1:
        key = head if keep_choice_leaf else (head[:-3] + "String" if head.endswith("[x]") else head)
        return {key: leaf_val}
    key = head[:-3] + "String" if head.endswith("[x]") else head
    return {key: _build_node_with_path(parts[1:], leaf_val, keep_choice_leaf=keep_choice_leaf)}


def _set_nested(target: dict[str, Any], parts: tuple[str, ...], val: Any) -> None:
    cur = target
    for seg in parts[:-1]:
        key = seg[:-3] + "String" if seg.endswith("[x]") else seg
        if key not in cur or not isinstance(cur[key], dict):
            cur[key] = {}
        cur = cur[key]
    last = parts[-1][:-3] + "String" if parts[-1].endswith("[x]") else parts[-1]
    cur[last] = val


def _build_slice_doc(sl: CompiledSlice) -> dict[str, Any]:
    item: Any = {}
    for matcher in sl.matchers:
        if not matcher.sub_parts:
            item = matcher.expected
        else:
            _set_nested(item, matcher.sub_parts, matcher.expected)
    items_list = [item for _ in range(sl.min_count)]
    doc: dict[str, Any] = {}
    _set_nested(doc, sl.parts, items_list)
    return doc


_ALL_PROFILES: list[tuple[str, CompiledProfile]] = sorted(COMPILED_PROFILES.items())

_REQUIRED_CASES: list[tuple[str, str, PathRule]] = [
    (url, prof.base_type or "Patient", rule)
    for url, prof in _ALL_PROFILES
    for rule in prof.required
    if rule.parts
]

_FORBIDDEN_CASES: list[tuple[str, str, PathRule]] = [
    (url, prof.base_type or "Patient", rule)
    for url, prof in _ALL_PROFILES
    for rule in prof.forbidden
    if rule.parts
]

_FIXED_CASES: list[tuple[str, str, ValueRule]] = [
    (url, prof.base_type or "Patient", rule) for url, prof in _ALL_PROFILES for rule in prof.fixed
]

_PATTERN_CASES: list[tuple[str, str, ValueRule]] = [
    (url, prof.base_type or "Patient", rule) for url, prof in _ALL_PROFILES for rule in prof.pattern
]

_NARROWING_CASES: list[tuple[str, str, TypeNarrowingRule]] = [
    (url, prof.base_type or "Patient", rule)
    for url, prof in _ALL_PROFILES
    for rule in prof.type_narrowing
]

_BINDING_CASES: list[tuple[str, str, AllowedValuesRule]] = [
    (url, prof.base_type or "Patient", rule)
    for url, prof in _ALL_PROFILES
    for rule in prof.bindings
]

_SLICE_CASES: list[tuple[str, str, CompiledSlice]] = [
    (url, prof.base_type or "Patient", sl) for url, prof in _ALL_PROFILES for sl in prof.slices
]


def test_all_183_ig_profiles_compiled_across_five_igs() -> None:
    """Verify all 183 resource + 15 datatype/extra StructureDefinition profiles are compiled."""
    assert len(PROFILE_CONSTRAINTS) == 198
    assert len(COMPILED_PROFILES) == 198
    resource_profiles = {
        u: s for u, s in PROFILE_CONSTRAINTS.items() if s["base_type"] in RESOURCE_MODELS
    }
    ca_base = [u for u in resource_profiles if "ca/baseline" in u]
    ca_core = [u for u in resource_profiles if "infoway" in u or "ca-core" in u]
    ips = [u for u in resource_profiles if "/uv/ips/" in u]
    us_core = [u for u in resource_profiles if "/us/core/" in u]
    r4_core = [u for u in resource_profiles if u not in (*ca_base, *ca_core, *ips, *us_core)]
    assert len(r4_core) == 46
    assert len(ca_base) == 27
    assert len(ca_core) == 31
    assert len(ips) == 27
    assert len(us_core) == 54


def _verify_profile_cardinality_and_targets(
    url: str,
    rtype: str,
    prof: CompiledProfile,
) -> None:
    for r_max in prof.max_one:
        if not r_max.parts:
            continue
        bad_max = _build_node_with_path(r_max.parts, ["a", "b"], keep_choice_leaf=True)
        assert any(
            f"element '{r_max.path}' exceeds max cardinality 1" in i
            for i in validate_single_profile(bad_max, rtype, url)
        )
        ok_max = _build_node_with_path(r_max.parts, ["a"], keep_choice_leaf=True)
        assert not any(
            f"element '{r_max.path}' exceeds max cardinality 1" in i
            for i in validate_single_profile(ok_max, rtype, url)
        )

    for r_tgt in prof.target_types:
        disallowed = (
            "VisionPrescription"
            if "VisionPrescription" not in r_tgt.allowed
            else "SubstanceNucleicAcid"
        )
        bad_ref = _build_node_with_path(r_tgt.parts, {"reference": f"{disallowed}/1"})
        assert any(
            f"'{r_tgt.path}' reference target '{disallowed}' not in" in i
            for i in validate_single_profile(bad_ref, rtype, url)
        )
        allowed_rt = next(iter(r_tgt.allowed))
        ok_ref = _build_node_with_path(r_tgt.parts, {"reference": f"{allowed_rt}/1"})
        assert not any(
            f"'{r_tgt.path}' reference target" in i
            for i in validate_single_profile(ok_ref, rtype, url)
        )


@pytest.mark.parametrize(
    ("url", "prof"),
    _ALL_PROFILES,
    ids=[_profile_short_id(u) for u, _ in _ALL_PROFILES],
)
def test_every_compiled_ig_profile_type_guard_max_one_and_targets(
    url: str,
    prof: CompiledProfile,
) -> None:
    """Every compiled IG profile enforces base_type, max_one cardinality, and targetProfile."""
    assert prof.base_type is not None
    assert prof.base_type in RESOURCE_MODELS or hasattr(fhir_types, prof.base_type)
    rtype = prof.base_type
    wrong_rtype = "Observation" if rtype != "Observation" else "Patient"
    mismatch = validate_single_profile({"resourceType": wrong_rtype}, wrong_rtype, url)
    assert mismatch == [f"Profile[{url}]: profile applies to '{rtype}', got '{wrong_rtype}'"]
    _verify_profile_cardinality_and_targets(url, rtype, prof)


@pytest.mark.parametrize(
    ("url", "rtype", "rule"),
    _REQUIRED_CASES,
    ids=[f"{_profile_short_id(u)}:{r.path}" for u, _, r in _REQUIRED_CASES],
)
def test_every_ig_profile_required_constraint(url: str, rtype: str, rule: PathRule) -> None:
    """Every min>=1 required constraint across all 183 IG profiles rejects omission and passes."""
    parent_doc = {} if len(rule.parts) == 1 else _build_node_with_path(rule.parts[:-1], {})
    neg = validate_single_profile(parent_doc, rtype, url)
    assert any(f"missing required element '{rule.path}'" in i for i in neg)

    pos_doc = _build_node_with_path(rule.parts, "present")
    pos = validate_single_profile(pos_doc, rtype, url)
    assert not any(f"missing required element '{rule.path}'" in i for i in pos)


@pytest.mark.parametrize(
    ("url", "rtype", "rule"),
    _FORBIDDEN_CASES,
    ids=[f"{_profile_short_id(u)}:{r.path}" for u, _, r in _FORBIDDEN_CASES],
)
def test_every_ig_profile_forbidden_constraint(url: str, rtype: str, rule: PathRule) -> None:
    """Every max=0 forbidden constraint across all 183 IG profiles rejects present elements."""
    neg_doc = _build_node_with_path(rule.parts, "disallowed")
    neg = validate_single_profile(neg_doc, rtype, url)
    assert any(f"forbidden element '{rule.path}'" in i for i in neg)

    pos = validate_single_profile({}, rtype, url)
    assert not any(f"forbidden element '{rule.path}'" in i for i in pos)


@pytest.mark.parametrize(
    ("url", "rtype", "rule"),
    _FIXED_CASES,
    ids=[f"{_profile_short_id(u)}:{r.path}" for u, _, r in _FIXED_CASES],
)
def test_every_ig_profile_fixed_value_constraint(url: str, rtype: str, rule: ValueRule) -> None:
    """Every fixed[x] constraint across all 183 IG profiles enforces exact value equality."""
    neg_doc = _build_node_with_path(rule.parts, "__wrong_fixed_value__")
    neg = validate_single_profile(neg_doc, rtype, url)
    assert any(f"'{rule.path}' must equal fixed value" in i for i in neg)

    pos_doc = _build_node_with_path(rule.parts, rule.expected)
    pos = validate_single_profile(pos_doc, rtype, url)
    assert not any(f"'{rule.path}' must equal fixed value" in i for i in pos)


@pytest.mark.parametrize(
    ("url", "rtype", "rule"),
    _PATTERN_CASES,
    ids=[f"{_profile_short_id(u)}:{r.path}" for u, _, r in _PATTERN_CASES],
)
def test_every_ig_profile_pattern_constraint(url: str, rtype: str, rule: ValueRule) -> None:
    """Every pattern[x] constraint across all 183 IG profiles enforces subset matching."""
    neg_doc = _build_node_with_path(rule.parts, "__wrong_pattern_value__")
    neg = validate_single_profile(neg_doc, rtype, url)
    assert any(f"'{rule.path}' does not match required pattern" in i for i in neg)

    pos_val = (
        {**rule.expected, "extraAllowedKey": "subset-ok"}
        if isinstance(rule.expected, dict)
        else rule.expected
    )
    pos_doc = _build_node_with_path(rule.parts, pos_val)
    pos = validate_single_profile(pos_doc, rtype, url)
    assert not any(f"'{rule.path}' does not match required pattern" in i for i in pos)


@pytest.mark.parametrize(
    ("url", "rtype", "rule"),
    _NARROWING_CASES,
    ids=[f"{_profile_short_id(u)}:{r.path}" for u, _, r in _NARROWING_CASES],
)
def test_every_ig_profile_choice_type_narrowing(
    url: str,
    rtype: str,
    rule: TypeNarrowingRule,
) -> None:
    """Every choice [x] type narrowing constraint across all 183 IG profiles is enforced."""
    bad_leaf = {f"{rule.stem}DisallowedChoiceType": "val"}
    neg_doc = (
        bad_leaf if not rule.parent_parts else _build_node_with_path(rule.parent_parts, bad_leaf)
    )
    neg = validate_single_profile(neg_doc, rtype, url)
    assert any(f"'{rule.path}' narrowed to" in i for i in neg)

    ok_leaf = {f"{rule.stem}{rule.allowed_suffixes[0]}": "val"}
    pos_doc = (
        ok_leaf if not rule.parent_parts else _build_node_with_path(rule.parent_parts, ok_leaf)
    )
    pos = validate_single_profile(pos_doc, rtype, url)
    assert not any(f"'{rule.path}' narrowed to" in i for i in pos)


@pytest.mark.parametrize(
    ("url", "rtype", "rule"),
    _BINDING_CASES,
    ids=[f"{_profile_short_id(u)}:{r.path}" for u, _, r in _BINDING_CASES],
)
def test_every_ig_profile_required_valueset_binding(
    url: str,
    rtype: str,
    rule: AllowedValuesRule,
) -> None:
    """Every required ValueSet binding across all 183 IG profiles rejects unknown codes."""
    neg_doc = _build_node_with_path(rule.parts, "__invalid_bound_code__")
    neg = validate_single_profile(neg_doc, rtype, url)
    assert any(
        f"'{rule.path}' code '__invalid_bound_code__' not in required ValueSet" in i for i in neg
    )

    good_code = next(iter(rule.allowed))
    pos_doc = _build_node_with_path(rule.parts, good_code)
    pos = validate_single_profile(pos_doc, rtype, url)
    assert not any(f"'{rule.path}' code" in i and "not in required ValueSet" in i for i in pos)


@pytest.mark.parametrize(
    ("url", "rtype", "sl"),
    _SLICE_CASES,
    ids=[f"{_profile_short_id(u)}:{s.path}:{idx}" for idx, (u, _, s) in enumerate(_SLICE_CASES)],
)
def test_every_ig_profile_slice_discriminator(
    url: str,
    rtype: str,
    sl: CompiledSlice,
) -> None:
    """Every discriminator slice across all 183 IG profiles enforces min count and matchers."""
    neg = validate_single_profile({}, rtype, url)
    assert any(f"slice at '{sl.path}' requires at least {sl.min_count}" in i for i in neg)

    pos_doc = _build_slice_doc(sl)
    assert _check_slices(pos_doc, url, (sl,)) == []
