"""Runtime Implementation Guide (IG) loader and StructureDefinition compiler."""

from __future__ import annotations

import json
import re
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fhirlance.profile_engine import COMPILED_PROFILES, CompiledProfile, compile_profiles
from fhirlance.profiles import COMPLETE_CODE_SYSTEMS, PROFILE_CONSTRAINTS, VALUE_SET_SPECS
from fhirlance.resources import RESOURCE_MODELS

if TYPE_CHECKING:
    from collections.abc import Sequence

__all__ = [
    "clear_ig_cache",
    "load_compiled_ig_profiles",
    "load_raw_ig_profiles",
    "register_ig",
]

_CHOICE_SUFFIX = "[x]"
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


@dataclass
class _ProfileAccumulator:
    required: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    max_one: list[str] = field(default_factory=list)
    fixed: dict[str, Any] = field(default_factory=dict)
    pattern: dict[str, Any] = field(default_factory=dict)
    type_narrowing: dict[str, list[str]] = field(default_factory=dict)
    target_types: dict[str, list[str]] = field(default_factory=dict)
    bindings: dict[str, list[str]] = field(default_factory=dict)
    binding_specs: dict[str, dict[str, Any]] = field(default_factory=dict)
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


def _extract_code_systems(cs_list: list[dict[str, Any]]) -> dict[str, list[str]]:
    code_systems: dict[str, list[str]] = {}
    for cs in cs_list:
        url = cs.get("url")
        if not url:
            continue
        codes: list[str] = []
        concepts = cs.get("concept") or []
        _collect_concepts(concepts, codes)
        if codes:
            code_systems[url] = codes
    return code_systems


def _extract_include_spec(
    inc: dict[str, Any],
    code_systems: dict[str, list[str]],
    codes: list[str],
    system_codes: dict[str, list[str]],
    external_systems: list[str],
) -> None:
    system = inc.get("system")
    concepts = inc.get("concept") or []
    if concepts:
        c_codes = [c["code"] for c in concepts if isinstance(c, dict) and "code" in c]
        codes.extend(c_codes)
        if system:
            system_codes.setdefault(system, []).extend(c_codes)
    elif system and not inc.get("filter"):
        sys_c = code_systems.get(system) or COMPLETE_CODE_SYSTEMS.get(system, [])
        if sys_c:
            codes.extend(sys_c)
            system_codes.setdefault(system, []).extend(sys_c)
        else:
            external_systems.append(system)


def _extract_value_sets(
    vs_list: list[dict[str, Any]],
    code_systems: dict[str, list[str]],
    vs_specs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, list[str]]:
    value_sets: dict[str, list[str]] = {}
    for vs in vs_list:
        url = vs.get("url")
        if not url:
            continue
        codes: list[str] = []
        system_codes: dict[str, list[str]] = {}
        external_systems: list[str] = []
        for inc in (vs.get("compose") or {}).get("include") or []:
            if isinstance(inc, dict):
                _extract_include_spec(inc, code_systems, codes, system_codes, external_systems)
        if not codes:
            _collect_expansion_codes((vs.get("expansion") or {}).get("contains") or [], codes)
        if codes:
            sorted_codes = sorted(set(codes))
            value_sets[url] = sorted_codes
            if vs_specs is not None:
                vs_specs[url] = {
                    "codes": sorted_codes,
                    "system_codes": {s: sorted(set(c)) for s, c in system_codes.items()},
                    "external_systems": sorted(set(external_systems)),
                }
        elif vs_specs is not None and (system_codes or external_systems):
            vs_specs[url] = {
                "codes": [],
                "system_codes": {s: sorted(set(c)) for s, c in system_codes.items()},
                "external_systems": sorted(set(external_systems)),
            }
    return value_sets


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
        if type_entry.get("code") == "Reference":
            targets = type_entry.get("targetProfile") or []
            allowed = sorted(
                {
                    resolved
                    for tp in targets
                    if (resolved := _resolve_target_profile(tp, sd_type_by_url))
                }
            )
            if allowed:
                acc.target_types[path] = allowed


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
    if strength in ("required", "extensible") and raw_vs:
        vs_url = raw_vs.split("|", maxsplit=1)[0]
        rel_path = path.split(".", 1)[1] if "." in path else path
        spec_entry = vs_specs.get(vs_url) or VALUE_SET_SPECS.get(vs_url)
        acc.binding_specs[rel_path] = {
            "strength": strength,
            "value_set": vs_url,
            "vs_spec": spec_entry,
        }
        if strength == "required" and vs_url in value_sets:
            acc.bindings[path] = value_sets[vs_url]


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
    if el.get("max") == "0":
        acc.forbidden.append(path)
    elif el.get("max") == "1":
        acc.max_one.append(path)

    fixed, pattern = _extract_fixed_or_pattern(el)
    if fixed is not None:
        acc.fixed[path] = fixed
    if pattern is not None:
        acc.pattern[path] = pattern

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
    if el.get("max") == "0" and base_max != "0":
        acc.forbidden.append(path)
    elif el.get("max") == "1" and base_max == "*":
        acc.max_one.append(path)

    fixed, pattern = _extract_fixed_or_pattern(el)
    b_fixed, b_pattern = _extract_fixed_or_pattern(base_el)
    if fixed is not None and fixed != b_fixed:
        acc.fixed[path] = fixed
    if pattern is not None and pattern != b_pattern:
        acc.pattern[path] = pattern

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

    return {
        "base_type": sd.get("type"),
        "base_definition": sd.get("baseDefinition"),
        "required": sorted(set(acc.required)),
        "forbidden": sorted(set(acc.forbidden)),
        "max_one": sorted(set(acc.max_one)),
        "fixed": acc.fixed,
        "pattern": acc.pattern,
        "type_narrowing": acc.type_narrowing,
        "target_types": acc.target_types,
        "bindings": acc.bindings,
        "binding_specs": acc.binding_specs,
        "slices": [s for s in acc.slices.values() if s["min"] >= 1 and s["matchers"]],
    }


def _merge_profile_with_parent(
    spec: dict[str, Any],
    parent: dict[str, Any] | None,
) -> dict[str, Any]:
    p_req = set(parent["required"]) if parent and "required" in parent else set()
    p_forb = set(parent["forbidden"]) if parent and "forbidden" in parent else set()
    p_max1 = set(parent["max_one"]) if parent and "max_one" in parent else set()

    p_fixed = parent.get("fixed", {}) if parent else {}
    p_pat = parent.get("pattern", {}) if parent else {}
    p_narr = parent.get("type_narrowing", {}) if parent else {}
    p_tgt = parent.get("target_types", {}) if parent else {}
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
        "forbidden": sorted(p_forb | set(spec.get("forbidden", []))),
        "max_one": sorted(p_max1 | set(spec.get("max_one", []))),
        "fixed": {**p_fixed, **spec.get("fixed", {})},
        "pattern": {**p_pat, **spec.get("pattern", {})},
        "type_narrowing": {**p_narr, **spec.get("type_narrowing", {})},
        "target_types": {**p_tgt, **spec.get("target_types", {})},
        "bindings": {**p_bind, **spec.get("bindings", {})},
        "binding_specs": merged_bs,
        "slices": [*p_sl, *spec.get("slices", [])],
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

    cached = _find_cached_package(str(source))
    if cached is not None:
        return cached

    raise FileNotFoundError(f"IG source not found: {source}")


def load_raw_ig_profiles(sources: Sequence[str | Path]) -> dict[str, dict[str, Any]]:
    """Load StructureDefinition profiles from IG sources and resolve inheritance."""
    container = _IGResources()
    for src in sources:
        path = _resolve_source_path(src)
        _load_source(path, container)

    code_systems = _extract_code_systems(container.code_systems)
    vs_specs: dict[str, dict[str, Any]] = {}
    value_sets = _extract_value_sets(container.value_sets, code_systems, vs_specs)

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
_COMPILED_CACHE: dict[tuple[tuple[str, int, int], ...], dict[str, CompiledProfile]] = {}


def clear_ig_cache() -> None:
    """Clear the compiled IG profiles cache and reset COMPILED_PROFILES."""
    _COMPILED_CACHE.clear()
    COMPILED_PROFILES.clear()
    COMPILED_PROFILES.update(_BASE_COMPILED_PROFILES)


def register_ig(sources: Sequence[str | Path]) -> dict[str, CompiledProfile]:
    """Compile IG sources and register them globally in COMPILED_PROFILES."""
    compiled = load_compiled_ig_profiles(sources)
    COMPILED_PROFILES.update(compiled)
    return dict(COMPILED_PROFILES)


def load_compiled_ig_profiles(
    sources: Sequence[str | Path],
) -> dict[str, CompiledProfile]:
    """Load, compile, and merge IG profiles with built-in COMPILED_PROFILES."""
    resolved_sources = [_resolve_source_path(s) for s in sources]
    cache_key = tuple(_fingerprint_source(p) for p in resolved_sources)
    if cache_key in _COMPILED_CACHE:
        return dict(_COMPILED_CACHE[cache_key])

    raw_profiles = load_raw_ig_profiles(sources)
    compiled_new = compile_profiles(raw_profiles)
    merged = dict(COMPILED_PROFILES)
    merged.update(compiled_new)
    _COMPILED_CACHE[cache_key] = merged
    return dict(merged)
