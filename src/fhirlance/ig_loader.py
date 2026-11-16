"""Runtime Implementation Guide (IG) loader and StructureDefinition compiler."""

from __future__ import annotations

import json
import re
import tarfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fhirlance.conceptmap import ConceptMapRegistry
from fhirlance.extension_spec import extract_extension_spec, resolve_all_extensions
from fhirlance.extensions import (
    _RAW_BUILTIN_EXTENSIONS,
    COMPILED_EXTENSIONS,
    CompiledExtension,
    compile_extensions,
)
from fhirlance.pkg_manager import find_package_dir, resolve_transitive_packages
from fhirlance.profile_engine import COMPILED_PROFILES, CompiledProfile, compile_profiles
from fhirlance.profiles import COMPLETE_CODE_SYSTEMS, PROFILE_CONSTRAINTS, VALUE_SET_SPECS
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.slicing_spec import extract_slice_groups, merge_slice_groups
from fhirlance.vs_expansion import (
    CodeSystemHierarchy,
    expand_value_set_codes,
    merge_code_system_supplements,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

__all__ = [
    "clear_ig_cache",
    "load_compiled_ig_bundle",
    "load_compiled_ig_extensions",
    "load_compiled_ig_profiles",
    "load_ig_concept_maps",
    "load_raw_ig_extensions",
    "load_raw_ig_profiles",
    "register_ig",
]

_CHOICE_SUFFIX = "[x]"
_CHOICE_SUFFIX_LEN = len(_CHOICE_SUFFIX)
_MAX_FHIR_STRING_LENGTH = 1_048_576
_MAX_SNAPSHOT_TYPE_NARROWING = 4
_MAX_TAR_MEMBER_BYTES = 25 * 1024 * 1024  # 25 MB
_MAX_TAR_MEMBERS = 5000

# Pre-sorted resource model names by descending length for longest-match-first resolution
_SORTED_RESOURCE_MODELS: tuple[str, ...] = tuple(
    sorted(RESOURCE_MODELS.keys(), key=len, reverse=True)
)

_VsData = tuple[dict[str, list[str]], dict[str, dict[str, Any]]] | dict[str, list[str]]


def _unpack_vs_data(vs_data: _VsData) -> tuple[dict[str, list[str]], dict[str, dict[str, Any]]]:
    if isinstance(vs_data, tuple):
        return vs_data
    return vs_data, {}


@dataclass
class _IGResources:
    code_systems: list[dict[str, Any]] = field(default_factory=list)
    value_sets: list[dict[str, Any]] = field(default_factory=list)
    structure_definitions: list[dict[str, Any]] = field(default_factory=list)
    concept_maps: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class _ProfileAccumulator:
    required: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    max_one: list[str] = field(default_factory=list)
    must_support: list[str] = field(default_factory=list)
    fixed: dict[str, Any] = field(default_factory=dict)
    pattern: dict[str, Any] = field(default_factory=dict)
    max_length: dict[str, int] = field(default_factory=dict)
    min_values: dict[str, Any] = field(default_factory=dict)
    max_values: dict[str, Any] = field(default_factory=dict)
    type_narrowing: dict[str, list[str]] = field(default_factory=dict)
    element_profiles: dict[str, list[str]] = field(default_factory=dict)
    target_types: dict[str, list[str]] = field(default_factory=dict)
    target_profiles: dict[str, list[str]] = field(default_factory=dict)
    target_aggregations: dict[str, list[str]] = field(default_factory=dict)
    bindings: dict[str, list[str]] = field(default_factory=dict)
    binding_specs: dict[str, dict[str, Any]] = field(default_factory=dict)
    preferred_bindings: dict[str, str | dict[str, Any]] = field(default_factory=dict)
    slices: dict[str, dict[str, Any]] = field(default_factory=dict)


def _collect_concepts(concepts: Sequence[Any], out: list[str]) -> None:
    for concept in concepts:
        if not isinstance(concept, dict):
            continue
        code = concept.get("code")
        if code:
            out.append(code)
        sub_concepts = concept.get("concept") or []
        if isinstance(sub_concepts, list):
            _collect_concepts(sub_concepts, out)


def _collect_expansion_codes(contains: Sequence[Any], out: list[str]) -> None:
    for item in contains:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        if code:
            out.append(code)
        sub_contains = item.get("contains") or []
        if isinstance(sub_contains, list):
            _collect_expansion_codes(sub_contains, out)


_BUILTIN_CS_HIERARCHIES: dict[str, CodeSystemHierarchy] = {
    url: CodeSystemHierarchy(
        codes=frozenset(codes),
        descendants={},
        children={},
        ancestors={},
        property_values={},
    )
    for url, codes in COMPLETE_CODE_SYSTEMS.items()
}


def _extract_code_systems(cs_list: list[dict[str, Any]]) -> dict[str, list[str]]:
    code_systems: dict[str, list[str]] = {}
    for cs in cs_list:
        url = cs.get("url")
        if not isinstance(url, str) or not url:
            continue
        codes: list[str] = []
        concepts = cs.get("concept") or []
        _collect_concepts(concepts, codes)
        if codes:
            base_url, _, embedded_ver = url.partition("|")
            raw_ver = cs.get("version")
            ver = raw_ver if isinstance(raw_ver, str) and raw_ver else embedded_ver
            code_systems[base_url] = codes
            if ver:
                code_systems[f"{base_url}|{ver}"] = codes
    return code_systems


def _build_hierarchies_from_codes(
    code_systems: Mapping[str, Sequence[str]],
) -> dict[str, CodeSystemHierarchy]:
    hierarchies = dict(_BUILTIN_CS_HIERARCHIES)
    for url, codes in code_systems.items():
        if url not in hierarchies:
            hierarchies[url] = CodeSystemHierarchy(
                codes=frozenset(codes),
                descendants={},
                children={},
                ancestors={},
                property_values={},
            )
    return hierarchies


def _collect_explicit_include_codes(
    vs: dict[str, Any],
    all_codes: frozenset[str],
) -> tuple[dict[str, set[str]], dict[str, str]]:
    explicit_by_sys: dict[str, set[str]] = {}
    sys_versions: dict[str, str] = {}
    compose = vs.get("compose")
    if isinstance(compose, dict):
        for inc in compose.get("include") or []:
            if not isinstance(inc, dict):
                continue
            raw_sys = inc.get("system")
            if not isinstance(raw_sys, str) or not raw_sys:
                continue
            sys_url, _, embedded_ver = raw_sys.partition("|")
            inc_ver = inc.get("version")
            effective_ver = inc_ver if isinstance(inc_ver, str) and inc_ver else embedded_ver
            if effective_ver:
                sys_versions[sys_url] = effective_ver
            concepts = inc.get("concept")
            if isinstance(concepts, list):
                c_codes = {
                    c["code"]
                    for c in concepts
                    if isinstance(c, dict) and isinstance(c.get("code"), str) and c["code"]
                }
                kept = c_codes & all_codes
                if kept:
                    explicit_by_sys.setdefault(sys_url, set()).update(kept)
    return explicit_by_sys, sys_versions


def _build_vs_spec(
    vs: dict[str, Any],
    all_codes: frozenset[str],
    systems: frozenset[str],
    hierarchies: Mapping[str, CodeSystemHierarchy],
) -> dict[str, Any]:
    explicit_by_sys, sys_versions = _collect_explicit_include_codes(vs, all_codes)
    system_codes: dict[str, list[str]] = {
        s: sorted(codes) for s, codes in explicit_by_sys.items() if codes
    }
    external_systems: list[str] = []

    for sys_url in sorted(systems):
        ver = sys_versions.get(sys_url, "")
        cs_hier = hierarchies.get(f"{sys_url}|{ver}") if ver else None
        if cs_hier is None:
            cs_hier = hierarchies.get(sys_url)
        if cs_hier is not None:
            matched = all_codes & cs_hier.codes
            if matched:
                merged = set(system_codes.get(sys_url, ())) | matched
                system_codes[sys_url] = sorted(merged)
        elif sys_url not in system_codes:
            external_systems.append(sys_url)

    return {
        "codes": sorted(all_codes),
        "system_codes": system_codes,
        "external_systems": sorted(set(external_systems)),
    }


def _vs_index_keys(vs: dict[str, Any]) -> list[str]:
    raw_url = vs.get("url")
    if not isinstance(raw_url, str) or not raw_url:
        return []
    base_url, _, embedded_ver = raw_url.partition("|")
    raw_ver = vs.get("version")
    ver = raw_ver if isinstance(raw_ver, str) and raw_ver else embedded_ver
    keys = [base_url]
    if ver:
        keys.append(f"{base_url}|{ver}")
    return keys


def _extract_value_sets(
    vs_list: list[dict[str, Any]],
    code_systems: dict[str, list[str]],
    vs_specs: dict[str, dict[str, Any]] | None = None,
    *,
    hierarchies: Mapping[str, CodeSystemHierarchy] | None = None,
) -> dict[str, list[str]]:
    eff_hierarchies = (
        hierarchies if hierarchies is not None else _build_hierarchies_from_codes(code_systems)
    )
    value_sets: dict[str, list[str]] = {}
    resolved_vs: dict[str, frozenset[str]] = {}
    incomplete_indices: list[int] = []

    for idx, vs in enumerate(vs_list):
        keys = _vs_index_keys(vs)
        if not keys:
            continue
        all_codes, systems, complete = expand_value_set_codes(vs, eff_hierarchies, resolved_vs)
        if not complete:
            incomplete_indices.append(idx)
        for key in keys:
            if all_codes:
                resolved_vs[key] = all_codes
        spec = _build_vs_spec(vs, all_codes, systems, eff_hierarchies)
        _store_vs_entry(keys, spec, value_sets, vs_specs)

    for idx in incomplete_indices:
        vs = vs_list[idx]
        keys = _vs_index_keys(vs)
        all_codes, systems, _ = expand_value_set_codes(vs, eff_hierarchies, resolved_vs)
        for key in keys:
            if all_codes:
                resolved_vs[key] = all_codes
        spec = _build_vs_spec(vs, all_codes, systems, eff_hierarchies)
        _store_vs_entry(keys, spec, value_sets, vs_specs)

    return value_sets


def _store_vs_entry(
    keys: list[str],
    spec: dict[str, Any],
    value_sets: dict[str, list[str]],
    vs_specs: dict[str, dict[str, Any]] | None,
) -> None:
    codes: list[str] = spec["codes"]
    if codes:
        for key in keys:
            value_sets[key] = codes
            if vs_specs is not None:
                vs_specs[key] = spec
    elif vs_specs is not None and (spec["system_codes"] or spec["external_systems"]):
        for key in keys:
            vs_specs[key] = spec


def _extract_fixed_or_pattern(el: dict[str, Any] | None) -> tuple[Any | None, Any | None]:
    if not el:
        return None, None
    fixed = next((v for k, v in el.items() if k.startswith("fixed")), None)
    pattern = next((v for k, v in el.items() if k.startswith("pattern")), None)
    return fixed, pattern


def _resolve_target_profile(tp: str, sd_type_by_url: dict[str, str]) -> str:
    url = tp.split("|", maxsplit=1)[0]
    if url in sd_type_by_url:
        return sd_type_by_url[url]
    if url in PROFILE_CONSTRAINTS and PROFILE_CONSTRAINTS[url].get("base_type"):
        return str(PROFILE_CONSTRAINTS[url]["base_type"])

    slug = url.rstrip("/").rsplit("/", 1)[-1]
    if slug in RESOURCE_MODELS:
        return slug

    # Match case-insensitively or as a token in the slug (longest match first)
    slug_tokens = [tok.lower() for tok in re.split(r"[-_.]", slug) if tok]
    slug_lower = slug.lower()
    for rtype in _SORTED_RESOURCE_MODELS:
        rt_lower = rtype.lower()
        if rt_lower == slug_lower or rt_lower in slug_tokens:
            return rtype

    for rtype in _SORTED_RESOURCE_MODELS:
        if rtype.lower() in slug_lower:
            return rtype

    return ""


def _record_slice_element(
    el: dict[str, Any],
    slices: dict[str, dict[str, Any]],
) -> None:
    el_id = el.get("id", "")
    parts = el_id.split(".")
    slice_seg_idx = next((i for i, seg in enumerate(parts) if ":" in seg), None)
    if slice_seg_idx is None:
        return

    slice_root_id = ".".join(parts[: slice_seg_idx + 1])
    slice_parent_path = ".".join(seg.split(":")[0] for seg in parts[: slice_seg_idx + 1])
    entry = slices.setdefault(
        slice_root_id,
        {"path": slice_parent_path, "min": 0, "max": None, "matchers": {}},
    )
    fixed, pattern = _extract_fixed_or_pattern(el)
    rel_sub = (
        ""
        if el_id == slice_root_id
        else ".".join(seg.split(":")[0] for seg in parts[slice_seg_idx + 1 :])
    )
    if el_id == slice_root_id:
        if el.get("min", 0) >= 1:
            entry["min"] = el["min"]
        if el.get("max") is not None:
            entry["max"] = el["max"]
    if fixed is not None:
        entry["matchers"][rel_sub] = ("fixed", fixed)
    if pattern is not None:
        entry["matchers"][rel_sub] = ("pattern", pattern)


def _record_reference_type(
    type_entry: dict[str, Any],
    path: str,
    sd_type_by_url: dict[str, str],
    acc: _ProfileAccumulator,
) -> None:
    targets = type_entry.get("targetProfile") or []
    allowed = sorted(
        {resolved for tp in targets if (resolved := _resolve_target_profile(tp, sd_type_by_url))}
    )
    if allowed:
        acc.target_types[path] = allowed
    profiles = sorted(
        {
            cleaned
            for tp in targets
            if isinstance(tp, str) and (cleaned := tp.split("|", 1)[0].strip())
        }
    )
    if profiles:
        acc.target_profiles[path] = profiles
    raw_aggs = type_entry.get("aggregation") or []
    aggs = sorted({a.strip() for a in raw_aggs if isinstance(a, str) and a.strip()})
    if aggs:
        acc.target_aggregations[path] = aggs


def _record_type_profile(
    type_entry: dict[str, Any],
    path: str,
    acc: _ProfileAccumulator,
) -> None:
    raw_profiles = type_entry.get("profile")
    if not isinstance(raw_profiles, list) or not raw_profiles:
        return
    cleaned = sorted(
        {
            p.split("|", 1)[0].strip()
            for p in raw_profiles
            if isinstance(p, str) and p.split("|", 1)[0].strip()
        }
    )
    if not cleaned:
        return
    if path.endswith(_CHOICE_SUFFIX):
        t_code = type_entry.get("code")
        if not isinstance(t_code, str) or not t_code:
            return
        target_path = f"{path[:-_CHOICE_SUFFIX_LEN]}{t_code[0].upper()}{t_code[1:]}"
    else:
        target_path = path
    existing = acc.element_profiles.get(target_path, [])
    acc.element_profiles[target_path] = sorted(set(existing) | set(cleaned))


def _record_element_types(
    el: dict[str, Any],
    path: str,
    sd_type_by_url: dict[str, str],
    acc: _ProfileAccumulator,
) -> None:
    el_types = el.get("type") or []
    if path.endswith(_CHOICE_SUFFIX) and el_types:
        acc.type_narrowing[path] = [
            t["code"] for t in el_types if isinstance(t, dict) and t.get("code")
        ]
    for type_entry in el_types:
        if not isinstance(type_entry, dict):
            continue
        t_code = type_entry.get("code")
        if t_code == "Reference":
            _record_reference_type(type_entry, path, sd_type_by_url, acc)
        if t_code != "Extension":
            _record_type_profile(type_entry, path, acc)


def _record_element_binding(
    el: dict[str, Any],
    path: str,
    value_sets: dict[str, list[str]],
    vs_specs: dict[str, dict[str, Any]],
    acc: _ProfileAccumulator,
) -> None:
    binding = el.get("binding") or {}
    strength = binding.get("strength")
    raw_vs = binding.get("valueSet")
    if not isinstance(raw_vs, str) or not raw_vs:
        return
    vs_url = raw_vs.split("|", maxsplit=1)[0]
    rel_path = path.split(".", 1)[1] if "." in path else path
    spec_entry = (
        vs_specs.get(raw_vs)
        or vs_specs.get(vs_url)
        or VALUE_SET_SPECS.get(raw_vs)
        or VALUE_SET_SPECS.get(vs_url)
    )
    if strength in ("required", "extensible"):
        acc.binding_specs[rel_path] = {
            "strength": strength,
            "value_set": raw_vs,
            "vs_spec": spec_entry,
        }
        vs_codes = value_sets.get(raw_vs) or value_sets.get(vs_url)
        if strength == "required" and vs_codes is not None:
            acc.bindings[path] = vs_codes
    elif strength == "preferred":
        acc.preferred_bindings[rel_path] = (
            {"value_set": raw_vs, "vs_spec": spec_entry} if spec_entry else raw_vs
        )


def _record_value_bounds(
    el: dict[str, Any],
    path: str,
    acc: _ProfileAccumulator,
) -> None:
    max_len = el.get("maxLength")
    if (
        isinstance(max_len, int)
        and not isinstance(max_len, bool)
        and max_len > 0
        and max_len != _MAX_FHIR_STRING_LENGTH
    ):
        acc.max_length[path] = max_len
    for k, v in el.items():
        if v is None:
            continue
        if k.startswith("minValue") and len(k) > len("minValue"):
            acc.min_values[path] = v
        elif k.startswith("maxValue") and len(k) > len("maxValue"):
            acc.max_values[path] = v


def _record_differential_element(
    el: dict[str, Any],
    sd_type_by_url: dict[str, str],
    vs_data: _VsData,
    acc: _ProfileAccumulator,
) -> None:
    path = el.get("path", "")
    if "." not in path:
        return
    if ":" in el.get("id", ""):
        _record_slice_element(el, acc.slices)
        return

    if el.get("min", 0) >= 1:
        acc.required.append(path)
    is_forbidden = el.get("max") == "0"
    if is_forbidden:
        acc.forbidden.append(path)
    elif el.get("max") == "1":
        acc.max_one.append(path)
    if el.get("mustSupport") is True and not is_forbidden:
        acc.must_support.append(path)

    fixed, pattern = _extract_fixed_or_pattern(el)
    if fixed is not None:
        acc.fixed[path] = fixed
    if pattern is not None:
        acc.pattern[path] = pattern

    _record_value_bounds(el, path, acc)
    _record_element_types(el, path, sd_type_by_url, acc)
    value_sets, vs_specs = _unpack_vs_data(vs_data)
    _record_element_binding(el, path, value_sets, vs_specs, acc)


def _record_snapshot_element(
    el: dict[str, Any],
    base_elements: dict[str, dict[str, Any]],
    sd_type_by_url: dict[str, str],
    vs_data: _VsData,
    acc: _ProfileAccumulator,
) -> None:
    path = el.get("path", "")
    if "." not in path:
        return
    if ":" in el.get("id", ""):
        _record_slice_element(el, acc.slices)
        return

    base_el = base_elements.get(path)
    base_min = base_el.get("min", 0) if base_el else 0
    base_max = base_el.get("max") if base_el else None

    if el.get("min", 0) >= 1 and base_min == 0:
        acc.required.append(path)
    is_forbidden = el.get("max") == "0"
    if is_forbidden and base_max != "0":
        acc.forbidden.append(path)
    elif el.get("max") == "1" and base_max == "*":
        acc.max_one.append(path)
    if el.get("mustSupport") is True and not is_forbidden:
        acc.must_support.append(path)

    fixed, pattern = _extract_fixed_or_pattern(el)
    b_fixed, b_pattern = _extract_fixed_or_pattern(base_el)
    if fixed is not None and fixed != b_fixed:
        acc.fixed[path] = fixed
    if pattern is not None and pattern != b_pattern:
        acc.pattern[path] = pattern

    _record_value_bounds(el, path, acc)
    _record_element_types(el, path, sd_type_by_url, acc)
    value_sets, vs_specs = _unpack_vs_data(vs_data)
    _record_element_binding(el, path, value_sets, vs_specs, acc)


def _get_base_elements(
    raw_base_def: str | None,
    base_type: str | None,
    all_sds: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    base_def = raw_base_def.split("|", 1)[0] if isinstance(raw_base_def, str) else None
    if base_def and base_def in all_sds:
        snapshot = all_sds[base_def].get("snapshot") or {}
        return {
            el["path"]: el
            for el in (snapshot.get("element") or [])
            if isinstance(el, dict) and "path" in el
        }
    base_map: dict[str, dict[str, Any]] = {}
    if base_type and base_type in RESOURCE_MODELS:
        model = RESOURCE_MODELS[base_type]
        for field_name, field_info in model.model_fields.items():
            if field_name.startswith("_"):
                continue
            is_req = field_info.is_required()
            is_list = "list" in str(field_info.annotation)
            base_map[f"{base_type}.{field_name}"] = {
                "min": 1 if is_req else 0,
                "max": "*" if is_list else "1",
            }
    return base_map


def _extract_constraints(elements: Sequence[Any]) -> list[dict[str, str]]:
    constraints: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for el in elements:
        if not isinstance(el, dict):
            continue
        path = el.get("path", "")
        if not path:
            continue
        for c in el.get("constraint") or ():
            if not isinstance(c, dict):
                continue
            key = str(c.get("key") or "")
            severity = str(c.get("severity") or "")
            expression = str(c.get("expression") or "").strip()
            if not key or key == "ele-1" or not expression or severity not in ("error", "warning"):
                continue
            if (path, key) in seen:
                continue
            seen.add((path, key))
            constraints.append(
                {
                    "key": key,
                    "severity": severity,
                    "human": str(c.get("human") or ""),
                    "expression": expression,
                    "path": path,
                }
            )
    return constraints


def _merge_constraints(
    parent_constraints: list[dict[str, str]],
    child_constraints: list[dict[str, str]],
) -> list[dict[str, str]]:
    merged: dict[tuple[str, str], dict[str, str]] = {
        (c["path"], c["key"]): c for c in parent_constraints
    }
    for c in child_constraints:
        merged[(c["path"], c["key"])] = c
    return list(merged.values())


def _extract_profile_spec(
    sd: dict[str, Any],
    sd_type_by_url: dict[str, str],
    vs_data: _VsData,
    all_sds: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    acc = _ProfileAccumulator()
    diff = sd.get("differential") or {}
    diff_elements = diff.get("element") or []
    if diff_elements:
        for el in diff_elements:
            if isinstance(el, dict):
                _record_differential_element(el, sd_type_by_url, vs_data, acc)
    else:
        base_elements = _get_base_elements(sd.get("baseDefinition"), sd.get("type"), all_sds)
        snap = sd.get("snapshot") or {}
        for el in snap.get("element") or []:
            if isinstance(el, dict):
                _record_snapshot_element(el, base_elements, sd_type_by_url, vs_data, acc)

    snap = sd.get("snapshot") or {}
    for el in snap.get("element") or []:
        if not isinstance(el, dict):
            continue
        sp = el.get("path", "")
        if sp.endswith(_CHOICE_SUFFIX) and ":" not in el.get("id", ""):
            el_types = el.get("type") or []
            stypes = [t["code"] for t in el_types if isinstance(t, dict) and t.get("code")]
            if stypes and len(stypes) <= _MAX_SNAPSHOT_TYPE_NARROWING:
                acc.type_narrowing.setdefault(sp, stypes)

    forbidden = sorted(set(acc.forbidden))
    return {
        "base_type": sd.get("type"),
        "base_definition": sd.get("baseDefinition"),
        "required": sorted(set(acc.required)),
        "forbidden": forbidden,
        "max_one": sorted(set(acc.max_one)),
        "must_support": sorted(set(acc.must_support) - set(forbidden)),
        "fixed": acc.fixed,
        "pattern": acc.pattern,
        "max_length": acc.max_length,
        "min_values": acc.min_values,
        "max_values": acc.max_values,
        "type_narrowing": acc.type_narrowing,
        "element_profiles": acc.element_profiles,
        "target_types": acc.target_types,
        "target_profiles": acc.target_profiles,
        "target_aggregations": acc.target_aggregations,
        "bindings": acc.bindings,
        "binding_specs": acc.binding_specs,
        "preferred_bindings": acc.preferred_bindings,
        "constraints": _extract_constraints(
            diff_elements if diff_elements else (snap.get("element") or []),
        ),
        "slices": [s for s in acc.slices.values() if s["min"] >= 1 and s["matchers"]],
        "slice_groups": extract_slice_groups(
            diff_elements if diff_elements else (snap.get("element") or []),
        ),
    }


def _merge_max_length(
    parent_ml: dict[str, int],
    child_ml: dict[str, int],
) -> dict[str, int]:
    merged = dict(parent_ml)
    for path, val in child_ml.items():
        merged[path] = min(merged[path], val) if path in merged else val
    return merged


def _unwrap_bound_comparable(val: Any) -> int | float | str | None:
    if isinstance(val, dict):
        val = val.get("value")
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float, str)):
        return val
    return None


def _pick_tighter_bound(prev: Any, val: Any, *, take_max: bool) -> Any:
    comp_prev = _unwrap_bound_comparable(prev)
    comp_val = _unwrap_bound_comparable(val)
    if isinstance(comp_prev, (int, float)) and isinstance(comp_val, (int, float)):
        return val if (comp_val > comp_prev if take_max else comp_val < comp_prev) else prev
    if isinstance(comp_prev, str) and isinstance(comp_val, str):
        return val if (comp_val > comp_prev if take_max else comp_val < comp_prev) else prev
    return val


def _merge_bound_values(
    parent_vals: dict[str, Any],
    child_vals: dict[str, Any],
    *,
    take_max: bool,
) -> dict[str, Any]:
    merged = dict(parent_vals)
    for path, val in child_vals.items():
        merged[path] = (
            _pick_tighter_bound(merged[path], val, take_max=take_max) if path in merged else val
        )
    return merged


def _merge_profile_with_parent(
    spec: dict[str, Any],
    parent: dict[str, Any] | None,
) -> dict[str, Any]:
    p_req = set(parent["required"]) if parent and "required" in parent else set()
    p_forb = set(parent["forbidden"]) if parent and "forbidden" in parent else set()
    p_max1 = set(parent["max_one"]) if parent and "max_one" in parent else set()
    p_ms = set(parent.get("must_support", [])) if parent else set()
    merged_forb = p_forb | set(spec.get("forbidden", []))

    p_fixed = parent.get("fixed", {}) if parent else {}
    p_pat = parent.get("pattern", {}) if parent else {}
    p_narr = parent.get("type_narrowing", {}) if parent else {}
    p_ep = parent.get("element_profiles", {}) if parent else {}
    p_tgt = parent.get("target_types", {}) if parent else {}
    p_tp = parent.get("target_profiles", {}) if parent else {}
    p_ta = parent.get("target_aggregations", {}) if parent else {}
    p_bind = parent.get("bindings", {}) if parent else {}
    p_sl = parent.get("slices", []) if parent else []
    p_bs = parent.get("binding_specs", {}) if parent else {}

    merged_bs = {**p_bs, **spec.get("binding_specs", {})}
    for path, p_spec in p_bs.items():
        if p_spec.get("strength") == "required" and path in merged_bs:
            merged_bs[path] = {**merged_bs[path], "strength": "required"}

    return {
        "base_type": spec.get("base_type") or (parent.get("base_type") if parent else None),
        "base_definition": spec.get("base_definition"),
        "required": sorted(p_req | set(spec.get("required", []))),
        "forbidden": sorted(merged_forb),
        "max_one": sorted(p_max1 | set(spec.get("max_one", []))),
        "must_support": sorted((p_ms | set(spec.get("must_support", []))) - merged_forb),
        "fixed": {**p_fixed, **spec.get("fixed", {})},
        "pattern": {**p_pat, **spec.get("pattern", {})},
        "max_length": _merge_max_length(
            parent.get("max_length", {}) if parent else {},
            spec.get("max_length", {}),
        ),
        "min_values": _merge_bound_values(
            parent.get("min_values", {}) if parent else {},
            spec.get("min_values", {}),
            take_max=True,
        ),
        "max_values": _merge_bound_values(
            parent.get("max_values", {}) if parent else {},
            spec.get("max_values", {}),
            take_max=False,
        ),
        "type_narrowing": {**p_narr, **spec.get("type_narrowing", {})},
        "element_profiles": {**p_ep, **spec.get("element_profiles", {})},
        "target_types": {**p_tgt, **spec.get("target_types", {})},
        "target_profiles": {**p_tp, **spec.get("target_profiles", {})},
        "target_aggregations": {**p_ta, **spec.get("target_aggregations", {})},
        "bindings": {**p_bind, **spec.get("bindings", {})},
        "binding_specs": merged_bs,
        "preferred_bindings": {
            **(parent.get("preferred_bindings", {}) if parent else {}),
            **spec.get("preferred_bindings", {}),
        },
        "constraints": _merge_constraints(
            parent.get("constraints", []) if parent else [],
            spec.get("constraints", []),
        ),
        "slices": [*p_sl, *spec.get("slices", [])],
        "slice_groups": merge_slice_groups(
            parent.get("slice_groups", []) if parent else [],
            spec.get("slice_groups", []),
        ),
    }


def _resolve_profile(
    url: str,
    profiles: dict[str, dict[str, Any]],
    resolved: dict[str, dict[str, Any]],
    seen: set[str],
) -> dict[str, Any] | None:
    if url in resolved:
        return resolved[url]
    if url in seen:
        return None
    spec = profiles.get(url)
    if spec is None:
        clean_url = url.split("|", 1)[0]
        if clean_url in PROFILE_CONSTRAINTS:
            return PROFILE_CONSTRAINTS[clean_url]
        return None

    seen.add(url)
    raw_parent = spec.get("base_definition")
    parent_url = raw_parent.split("|", 1)[0] if isinstance(raw_parent, str) else None
    parent: dict[str, Any] | None = None
    if parent_url:
        if parent_url in profiles:
            parent = _resolve_profile(parent_url, profiles, resolved, seen)
        elif parent_url in PROFILE_CONSTRAINTS:
            parent = PROFILE_CONSTRAINTS[parent_url]

    merged = _merge_profile_with_parent(spec, parent)
    resolved[url] = merged
    return merged


def _resolve_all_profiles(profiles: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}
    for url in profiles:
        _resolve_profile(url, profiles, resolved, set())
    return resolved


def _ingest_resource(data: dict[str, Any], container: _IGResources) -> None:
    rt = data.get("resourceType")
    if rt == "Bundle":
        for entry in data.get("entry") or []:
            if isinstance(entry, dict):
                res = entry.get("resource")
                if isinstance(res, dict):
                    _ingest_resource(res, container)
    elif rt == "CodeSystem":
        container.code_systems.append(data)
    elif rt == "ValueSet":
        container.value_sets.append(data)
    elif rt == "StructureDefinition":
        container.structure_definitions.append(data)
    elif rt == "ConceptMap":
        container.concept_maps.append(data)


def _load_from_tarball(path: Path, container: _IGResources) -> None:
    member_count = 0
    with tarfile.open(path, "r:gz") as tar:
        for member in tar:
            member_count += 1
            if member_count > _MAX_TAR_MEMBERS:
                raise ValueError(f"Tarball exceeds maximum member limit of {_MAX_TAR_MEMBERS}")
            norm_name = member.name.replace("\\", "/")
            if norm_name.startswith("/") or ".." in norm_name.split("/"):
                continue
            if not member.isfile() or not norm_name.endswith(".json"):
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            raw_bytes = extracted.read(_MAX_TAR_MEMBER_BYTES + 1)
            if len(raw_bytes) > _MAX_TAR_MEMBER_BYTES:
                continue
            try:
                data = json.loads(raw_bytes.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(data, dict):
                _ingest_resource(data, container)


def _load_from_directory(dir_path: Path, container: _IGResources) -> None:
    pkg_dir = dir_path / "package"
    target_dir = pkg_dir if pkg_dir.is_dir() else dir_path
    json_files = list(target_dir.glob("*.json"))
    if not json_files and target_dir != dir_path:
        json_files = list(dir_path.glob("*.json"))

    for jf in json_files:
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(data, dict):
            _ingest_resource(data, container)


def _load_from_file(file_path: Path, container: _IGResources) -> None:
    suffixes = file_path.suffixes
    if any(s in (".tgz", ".gz") for s in suffixes):
        _load_from_tarball(file_path, container)
        return

    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return
    if isinstance(data, dict):
        _ingest_resource(data, container)


def _load_source(path: Path, container: _IGResources) -> None:
    if path.is_dir():
        _load_from_directory(path, container)
    elif path.is_file():
        _load_from_file(path, container)


def _pkg_sort_key(p: Path) -> tuple[Any, ...]:
    name = p.parent.name if p.name == "package" else p.name
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name))


def _find_cached_package(source_str: str) -> Path | None:
    cache_dir = Path.home() / ".fhir" / "packages"
    if not cache_dir.is_dir():
        return None

    if "#" in source_str:
        cand_pkg = cache_dir / source_str / "package"
        if cand_pkg.is_dir():
            return cand_pkg
        cand_dir = cache_dir / source_str
        return cand_dir if cand_dir.exists() else None

    matches = sorted(cache_dir.glob(f"{source_str}#*/package"), key=_pkg_sort_key)
    if matches:
        return matches[-1]

    dir_matches = sorted(cache_dir.glob(f"{source_str}#*"), key=_pkg_sort_key)
    if dir_matches:
        cand = dir_matches[-1]
        cand_pkg = cand / "package"
        return cand_pkg if cand_pkg.is_dir() else cand
    return None


def _resolve_source_path(source: str | Path) -> Path:
    local_path = Path(source)
    if local_path.exists():
        return local_path.resolve()

    source_str = str(source)
    cached = _find_cached_package(source_str)
    if cached is not None:
        return cached

    pkg_id, _, pkg_ver = source_str.partition("#")
    pkg_cached = find_package_dir(pkg_id, pkg_ver or None)
    if pkg_cached is not None:
        return pkg_cached

    raise FileNotFoundError(f"IG source not found: {source}")


def _resolve_sources_with_deps(sources: Sequence[str | Path]) -> list[Path]:
    direct = [_resolve_source_path(s) for s in sources]
    return resolve_transitive_packages(direct)


def load_raw_ig_profiles(sources: Sequence[str | Path]) -> dict[str, dict[str, Any]]:
    """Load StructureDefinition profiles from IG sources and resolve inheritance."""
    resolved_paths = _resolve_sources_with_deps(sources)
    value_sets, vs_specs, all_sds, sd_type_by_url = _load_ig_sds(resolved_paths)
    raw_profiles: dict[str, dict[str, Any]] = {}
    for url, sd in all_sds.items():
        if (
            sd.get("kind") not in ("resource", "complex-type")
            or sd.get("derivation") != "constraint"
        ):
            continue
        raw_profiles[url] = _extract_profile_spec(
            sd, sd_type_by_url, (value_sets, vs_specs), all_sds
        )

    return _resolve_all_profiles(raw_profiles)


def _fingerprint_source(path: Path) -> tuple[str, int, int]:
    if path.is_file():
        st = path.stat()
        return (str(path), st.st_mtime_ns, st.st_size)
    if path.is_dir():
        pkg = path / "package"
        target_dir = pkg if pkg.is_dir() else path
        json_files = list(target_dir.glob("*.json"))
        if not json_files and target_dir != path:
            json_files = list(path.glob("*.json"))
        if not json_files:
            st = path.stat()
            return (str(path), st.st_mtime_ns, 0)
        max_mtime = 0
        total_size = 0
        for f in json_files:
            st = f.stat()
            max_mtime = max(max_mtime, st.st_mtime_ns)
            total_size += st.st_size
        return (str(path), max_mtime, total_size)
    return (str(path), 0, 0)


_BASE_COMPILED_PROFILES: dict[str, CompiledProfile] = dict(COMPILED_PROFILES)
_BASE_COMPILED_EXTENSIONS: dict[str, CompiledExtension] = dict(COMPILED_EXTENSIONS)
_COMPILED_CACHE: dict[tuple[tuple[str, int, int], ...], dict[str, CompiledProfile]] = {}
_COMPILED_EXT_CACHE: dict[tuple[tuple[str, int, int], ...], dict[str, CompiledExtension]] = {}
_CONCEPT_MAP_CACHE: dict[tuple[tuple[str, int, int], ...], ConceptMapRegistry] = {}
_CACHE_LOCK = threading.Lock()


def _load_ig_resources(paths: Sequence[Path]) -> _IGResources:
    container = _IGResources()
    for path in resolve_transitive_packages(paths):
        _load_source(path, container)
    return container


def _load_ig_sds(
    paths: Sequence[Path],
) -> tuple[
    dict[str, list[str]],
    dict[str, dict[str, Any]],
    dict[str, dict[str, Any]],
    dict[str, str],
]:
    container = _load_ig_resources(paths)

    code_systems = _extract_code_systems(container.code_systems)
    hierarchies = _build_hierarchies_from_codes(code_systems)
    hierarchies.update(merge_code_system_supplements(container.code_systems))
    vs_specs: dict[str, dict[str, Any]] = {}
    value_sets = _extract_value_sets(
        container.value_sets, code_systems, vs_specs, hierarchies=hierarchies
    )

    all_sds: dict[str, dict[str, Any]] = {}
    sd_type_by_url: dict[str, str] = {}
    for sd in container.structure_definitions:
        url = sd.get("url")
        if url:
            all_sds[url] = sd
            clean_url = url.split("|", 1)[0]
            all_sds[clean_url] = sd
            sd_type = sd.get("type")
            if sd_type:
                sd_type_by_url[url] = sd_type
                sd_type_by_url[clean_url] = sd_type
    return value_sets, vs_specs, all_sds, sd_type_by_url


def load_raw_ig_extensions(sources: Sequence[str | Path]) -> dict[str, dict[str, Any]]:
    """Load Extension StructureDefinitions from IG sources and resolve inheritance."""
    resolved_paths = _resolve_sources_with_deps(sources)
    value_sets, vs_specs, all_sds, sd_type_by_url = _load_ig_sds(resolved_paths)
    raw_exts: dict[str, dict[str, Any]] = {}
    for url, sd in all_sds.items():
        if sd.get("type") == "Extension" and sd.get("derivation") == "constraint":
            raw_exts[url] = extract_extension_spec(sd, sd_type_by_url, value_sets, vs_specs)
    return resolve_all_extensions(raw_exts, _RAW_BUILTIN_EXTENSIONS)


def _extract_profiles_and_extensions(
    resolved_paths: Sequence[Path],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    value_sets, vs_specs, all_sds, sd_type_by_url = _load_ig_sds(resolved_paths)
    raw_profiles: dict[str, dict[str, Any]] = {}
    raw_exts: dict[str, dict[str, Any]] = {}
    for url, sd in all_sds.items():
        if sd.get("derivation") != "constraint":
            continue
        if sd.get("type") == "Extension":
            raw_exts[url] = extract_extension_spec(sd, sd_type_by_url, value_sets, vs_specs)
        elif sd.get("kind") in ("resource", "complex-type"):
            raw_profiles[url] = _extract_profile_spec(
                sd, sd_type_by_url, (value_sets, vs_specs), all_sds
            )
    return _resolve_all_profiles(raw_profiles), resolve_all_extensions(
        raw_exts, _RAW_BUILTIN_EXTENSIONS
    )


def load_compiled_ig_bundle(
    sources: Sequence[str | Path],
) -> tuple[dict[str, CompiledProfile], dict[str, CompiledExtension]]:
    """Load and compile both IG profiles and Extension StructureDefinitions in one pass."""
    resolved_sources = _resolve_sources_with_deps(sources)
    cache_key = tuple(_fingerprint_source(p) for p in resolved_sources)
    with _CACHE_LOCK:
        if cache_key in _COMPILED_CACHE and cache_key in _COMPILED_EXT_CACHE:
            return dict(_COMPILED_CACHE[cache_key]), dict(_COMPILED_EXT_CACHE[cache_key])

    raw_profiles, raw_exts = _extract_profiles_and_extensions(resolved_sources)
    merged_profiles = dict(_BASE_COMPILED_PROFILES)
    merged_profiles.update(compile_profiles(raw_profiles))
    merged_exts = dict(_BASE_COMPILED_EXTENSIONS)
    merged_exts.update(compile_extensions(raw_exts))

    with _CACHE_LOCK:
        _COMPILED_CACHE[cache_key] = merged_profiles
        _COMPILED_EXT_CACHE[cache_key] = merged_exts
    return dict(merged_profiles), dict(merged_exts)


def load_compiled_ig_extensions(
    sources: Sequence[str | Path],
) -> dict[str, CompiledExtension]:
    """Load, compile, and merge IG Extension StructureDefinitions with built-ins."""
    _, exts = load_compiled_ig_bundle(sources)
    return exts


def clear_ig_cache() -> None:
    """Clear the compiled IG profiles/extensions cache and reset globals."""
    with _CACHE_LOCK:
        _COMPILED_CACHE.clear()
        _COMPILED_EXT_CACHE.clear()
        _CONCEPT_MAP_CACHE.clear()
        COMPILED_PROFILES.clear()
        COMPILED_PROFILES.update(_BASE_COMPILED_PROFILES)
        COMPILED_EXTENSIONS.clear()
        COMPILED_EXTENSIONS.update(_BASE_COMPILED_EXTENSIONS)


def load_ig_concept_maps(ig_sources: Sequence[str | Path]) -> ConceptMapRegistry:
    """Load ConceptMap resources from IG sources into a cached ConceptMapRegistry."""
    resolved_sources = _resolve_sources_with_deps(ig_sources)
    cache_key = tuple(_fingerprint_source(p) for p in resolved_sources)
    with _CACHE_LOCK:
        cached = _CONCEPT_MAP_CACHE.get(cache_key)
        if cached is not None:
            return cached.copy()

    container = _load_ig_resources(resolved_sources)
    registry = ConceptMapRegistry()
    for cm in container.concept_maps:
        registry.register_dict(cm)

    with _CACHE_LOCK:
        _CONCEPT_MAP_CACHE[cache_key] = registry
    return registry.copy()


def register_ig(sources: Sequence[str | Path]) -> dict[str, CompiledProfile]:
    """Compile IG sources and register profiles and extensions globally."""
    compiled, compiled_exts = load_compiled_ig_bundle(sources)
    with _CACHE_LOCK:
        COMPILED_PROFILES.update(compiled)
        COMPILED_EXTENSIONS.update(compiled_exts)
        return dict(COMPILED_PROFILES)


def load_compiled_ig_profiles(
    sources: Sequence[str | Path],
) -> dict[str, CompiledProfile]:
    """Load, compile, and merge IG profiles with built-in COMPILED_PROFILES."""
    profiles, _ = load_compiled_ig_bundle(sources)
    return profiles
