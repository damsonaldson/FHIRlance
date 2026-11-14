"""Compiled IG StructureDefinition profile engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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


@dataclass(frozen=True, slots=True)
class CompiledSlice:
    """A minimum-cardinality slice rule with compiled matchers."""

    path: str
    parts: tuple[str, ...]
    min_count: int
    matchers: tuple[SliceMatcher, ...]


@dataclass(frozen=True, slots=True)
class CompiledBindingRule:
    """A compiled ValueSet binding constraint."""

    path: str
    parts: tuple[str, ...]
    strength: str
    value_set: str
    vs_spec: dict[str, Any] | None = None


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


def _check_child_present(parent_val: Any, child_seg: str) -> bool:
    if not isinstance(parent_val, dict):
        return False
    if child_seg.endswith(_CHOICE_SUFFIX):
        stem = child_seg[:-_CHOICE_SUFFIX_LEN]
        return any(
            k.startswith(stem) and not k.startswith("_") and parent_val[k] is not None
            for k in parent_val
        )
    return child_seg in parent_val and parent_val[child_seg] is not None


def _extract_ref_resource_type(ref_str: str) -> str | None:
    """Extract target resourceType from relative/absolute FHIR Reference strings."""
    if not ref_str or ref_str.startswith(("#", "urn:")):
        return None
    parts = ref_str.split("/")
    for segment in parts[:-1]:
        if segment in RESOURCE_MODELS:
            return segment
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
                        tuple(seg.split(":")[0] for seg in sub.split(".") if seg) if sub else (),
                        kind,
                        exp,
                    )
                    for sub, (kind, exp) in sl["matchers"].items()
                ),
            )
            for sl in spec.get("slices", ())
        ),
        binding_specs=_compile_binding_specs(
            base_type,
            spec.get("binding_specs", {}),
            spec.get("bindings", {}),
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


def _check_forbidden(
    resource: dict[str, Any], prof_url: str, rules: tuple[PathRule, ...]
) -> list[str]:
    return [
        f"Profile[{prof_url}]: forbidden element '{rule.path}' (max=0) is present"
        for rule in rules
        if resolve_nodes(resource, rule.parts)
    ]


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


def _check_target_types(
    resource: dict[str, Any], prof_url: str, rules: tuple[AllowedValuesRule, ...]
) -> list[str]:
    issues: list[str] = []
    for rule in rules:
        for ref_obj in resolve_nodes(resource, rule.parts):
            if isinstance(ref_obj, dict) and isinstance(ref_obj.get("reference"), str):
                ref_rt = _extract_ref_resource_type(ref_obj["reference"])
                if ref_rt is not None and ref_rt not in rule.allowed:
                    issues.append(
                        f"Profile[{prof_url}]: '{rule.path}' reference target "
                        f"'{ref_rt}' not in {sorted(rule.allowed)}"
                    )
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
    return issues


def validate_single_profile(
    resource: dict[str, Any],
    rtype: str,
    prof_url: str,
    compiled_profiles: dict[str, CompiledProfile] = COMPILED_PROFILES,
    **kwargs: Any,
) -> list[str]:
    """Validate a resource against a single compiled IG StructureDefinition constraint set."""
    spec = compiled_profiles.get(prof_url)
    if spec is None:
        return []

    if spec.base_type and spec.base_type != rtype:
        return [f"Profile[{prof_url}]: profile applies to '{spec.base_type}', got '{rtype}'"]

    tx_raw = kwargs.get("tx", "local")
    strict_extensible = bool(kwargs.get("strict_extensible", False))
    _warnings_out: list[str] | None = kwargs.get("_warnings_out")
    tx_options = (
        tx_raw
        if isinstance(tx_raw, TxOptions)
        else parse_tx_options(tx_raw, strict_extensible=strict_extensible)
    )

    return [
        *_check_required(resource, prof_url, spec.required),
        *_check_forbidden(resource, prof_url, spec.forbidden),
        *_check_max_one(resource, prof_url, spec.max_one),
        *_check_fixed(resource, prof_url, spec.fixed),
        *_check_pattern(resource, prof_url, spec.pattern),
        *_check_type_narrowing(resource, prof_url, spec.type_narrowing),
        *_check_target_types(resource, prof_url, spec.target_types),
        *_check_bindings(
            resource,
            prof_url,
            spec.binding_specs,
            tx_options,
            _warnings_out=_warnings_out,
        ),
        *_check_slices(resource, prof_url, spec.slices),
    ]
