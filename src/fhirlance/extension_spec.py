"""Pure Extraction and Inheritance Resolution for FHIR Extension StructureDefinitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Mapping

_CHOICE_PREFIX = "value"
_MAX_SNAPSHOT_VALUE_TYPES = 15
_MIN_SUBEXT_SEGMENTS = 3


@dataclass(frozen=True, slots=True)
class _ExtractCtx:
    sd_type_by_url: Mapping[str, str]
    value_sets: Mapping[str, list[str]]
    vs_specs: Mapping[str, dict[str, Any]] | None


def _empty_node_spec() -> dict[str, Any]:
    return {
        "url": None,
        "min": 0,
        "max": None,
        "value_forbidden": False,
        "value_required": False,
        "value_types": [],
        "value_binding": None,
        "value_target_types": [],
        "value_fixed": None,
        "has_value_fixed": False,
        "value_pattern": None,
        "extension_forbidden": False,
        "extension_required": False,
        "slicing_closed": False,
        "sub_extensions": {},
    }


def _extract_fixed_or_pattern(el: dict[str, Any]) -> tuple[bool, Any, Any]:
    for key, val in el.items():
        if key.startswith("fixed"):
            return True, val, None
    for key, val in el.items():
        if key.startswith("pattern"):
            return False, None, val
    return False, None, None


def _resolve_target_types(
    el_types: list[dict[str, Any]],
    sd_type_by_url: Mapping[str, str],
) -> list[str]:
    targets: set[str] = set()
    for type_entry in el_types:
        if type_entry.get("code") == "Reference":
            raw_targets = type_entry.get("targetProfile")
            if not isinstance(raw_targets, list):
                continue
            for tp in raw_targets:
                clean = str(tp).split("|", maxsplit=1)[0]
                resolved = sd_type_by_url.get(clean)
                if not resolved:
                    slug = clean.rstrip("/").rsplit("/", 1)[-1]
                    if slug and slug[0].isupper() and "-" not in slug:
                        resolved = slug
                if resolved:
                    targets.add(resolved)
    return sorted(targets)


def _extract_binding_spec(
    el: dict[str, Any],
    vs_specs: Mapping[str, dict[str, Any]] | None,
) -> dict[str, Any] | None:
    binding = el.get("binding")
    if not isinstance(binding, dict):
        return None
    strength = binding.get("strength")
    raw_vs = binding.get("valueSet")
    if strength not in ("required", "extensible") or not raw_vs:
        return None
    vs_url = str(raw_vs).split("|", maxsplit=1)[0]
    spec: dict[str, Any] = {"strength": strength, "value_set": vs_url}
    if vs_specs is not None and vs_url in vs_specs:
        spec["vs_spec"] = vs_specs[vs_url]
    return spec


def _apply_value_element(
    node: dict[str, Any],
    el: dict[str, Any],
    leaf: str,
    ctx: _ExtractCtx,
) -> None:
    if el.get("max") == "0":
        node["value_forbidden"] = True
    if el.get("min", 0) >= 1:
        node["value_required"] = True

    el_types = [t for t in (el.get("type") or ()) if isinstance(t, dict)]
    codes = [str(t["code"]) for t in el_types if t.get("code")]
    if codes and (leaf != "value[x]" or len(codes) <= _MAX_SNAPSHOT_VALUE_TYPES):
        node["value_types"] = codes
    elif not codes and leaf.startswith(_CHOICE_PREFIX) and leaf != "value[x]":
        suffix = leaf[len(_CHOICE_PREFIX) :]
        if suffix:
            node["value_types"] = [suffix[0].lower() + suffix[1:]]

    target_types = _resolve_target_types(el_types, ctx.sd_type_by_url)
    if target_types:
        node["value_target_types"] = target_types

    binding_spec = _extract_binding_spec(el, ctx.vs_specs)
    if binding_spec is not None:
        node["value_binding"] = binding_spec

    has_fixed, fixed_val, pattern_val = _extract_fixed_or_pattern(el)
    if has_fixed:
        node["has_value_fixed"] = True
        node["value_fixed"] = fixed_val
    if pattern_val is not None:
        node["value_pattern"] = pattern_val


def _apply_extension_list_element(node: dict[str, Any], el: dict[str, Any]) -> None:
    if el.get("max") == "0":
        node["extension_forbidden"] = True
    if el.get("min", 0) >= 1:
        node["extension_required"] = True
    slicing = el.get("slicing")
    if isinstance(slicing, dict) and slicing.get("rules") == "closed":
        node["slicing_closed"] = True


def _apply_slice_root(node: dict[str, Any], el: dict[str, Any]) -> None:
    if "min" in el and isinstance(el["min"], int):
        node["min"] = el["min"]
    raw_max = el.get("max")
    if raw_max == "*":
        node["max"] = None
    elif isinstance(raw_max, str) and raw_max.isdigit():
        node["max"] = int(raw_max)


def _navigate_slice_node(root: dict[str, Any], segments: list[str]) -> tuple[dict[str, Any], str]:
    """Walk `extension:<sliceName>` segments, returning target node and remaining leaf."""
    curr = root
    idx = 1
    while idx < len(segments):
        seg = segments[idx]
        if seg.startswith("extension:"):
            slice_name = seg.split(":", maxsplit=1)[1]
            sub_map: dict[str, dict[str, Any]] = curr["sub_extensions"]
            if slice_name not in sub_map:
                sub = _empty_node_spec()
                sub["url"] = slice_name
                sub_map[slice_name] = sub
            curr = sub_map[slice_name]
            idx += 1
            continue
        return curr, seg
    return curr, ""


def _record_element(
    root: dict[str, Any],
    el: dict[str, Any],
    ctx: _ExtractCtx,
) -> None:
    el_id = el.get("id") or el.get("path") or ""
    segments = el_id.split(".")
    if not segments or segments[0] != "Extension":
        return

    node, leaf = _navigate_slice_node(root, segments)
    if not leaf:
        if len(segments) > 1:
            _apply_slice_root(node, el)
        return

    if leaf == "url":
        fixed_url = el.get("fixedUri") or el.get("fixedString")
        if isinstance(fixed_url, str) and fixed_url and len(segments) >= _MIN_SUBEXT_SEGMENTS:
            node["url"] = fixed_url
        return

    if leaf == "extension":
        _apply_extension_list_element(node, el)
        return

    if leaf.startswith(_CHOICE_PREFIX):
        _apply_value_element(node, el, leaf, ctx)


def _detect_is_modifier(sd: dict[str, Any]) -> bool:
    for section in ("differential", "snapshot"):
        elements = (sd.get(section) or {}).get("element") or ()
        for el in elements:
            if isinstance(el, dict) and el.get("id") == "Extension" and "isModifier" in el:
                return bool(el["isModifier"])
    return False


def _extract_contexts(sd: dict[str, Any]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for ctx in sd.get("context") or ():
        if isinstance(ctx, dict):
            ctype = ctx.get("type")
            expr = ctx.get("expression")
            if isinstance(ctype, str) and ctype and isinstance(expr, str) and expr:
                out.append((ctype, expr))
    return out


def _rekey_sub_extensions(node: dict[str, Any]) -> None:
    """Re-key sub_extensions by their effective fixedUrl (falling back to slice name)."""
    rekeyed: dict[str, dict[str, Any]] = {}
    for slice_name, sub in node["sub_extensions"].items():
        _rekey_sub_extensions(sub)
        eff_url = sub.get("url") or slice_name
        sub["url"] = eff_url
        rekeyed[eff_url] = sub
    node["sub_extensions"] = rekeyed


def extract_extension_spec(
    sd: dict[str, Any],
    sd_type_by_url: Mapping[str, str],
    value_sets: Mapping[str, list[str]],
    vs_specs: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Extract a raw constraint spec dict from an Extension StructureDefinition."""
    root = _empty_node_spec()
    root["url"] = str(sd.get("url") or "").split("|", maxsplit=1)[0]

    ctx = _ExtractCtx(sd_type_by_url=sd_type_by_url, value_sets=value_sets, vs_specs=vs_specs)
    snap_elements = (sd.get("snapshot") or {}).get("element") or ()
    diff_elements = (sd.get("differential") or {}).get("element") or ()
    for el in snap_elements:
        if isinstance(el, dict):
            _record_element(root, el, ctx)
    for el in diff_elements:
        if isinstance(el, dict):
            _record_element(root, el, ctx)

    _rekey_sub_extensions(root)
    return {
        "url": root["url"],
        "base_definition": sd.get("baseDefinition"),
        "is_modifier": _detect_is_modifier(sd),
        "contexts": _extract_contexts(sd),
        "node": root,
    }


def _merge_node_specs(parent: dict[str, Any], child: dict[str, Any]) -> dict[str, Any]:
    merged_subs = dict(parent.get("sub_extensions") or {})
    for url, c_sub in (child.get("sub_extensions") or {}).items():
        if url in merged_subs:
            merged_subs[url] = _merge_node_specs(merged_subs[url], c_sub)
        else:
            merged_subs[url] = c_sub

    c_types = child.get("value_types") or []
    p_types = parent.get("value_types") or []
    c_targets = child.get("value_target_types") or []
    p_targets = parent.get("value_target_types") or []
    return {
        "url": child.get("url") or parent.get("url"),
        "min": child.get("min") if child.get("min", 0) > 0 else parent.get("min", 0),
        "max": child.get("max") if child.get("max") is not None else parent.get("max"),
        "value_forbidden": bool(parent.get("value_forbidden") or child.get("value_forbidden")),
        "value_required": bool(parent.get("value_required") or child.get("value_required")),
        "value_types": c_types if c_types else p_types,
        "value_binding": child.get("value_binding") or parent.get("value_binding"),
        "value_target_types": c_targets if c_targets else p_targets,
        "value_fixed": (
            child.get("value_fixed") if child.get("has_value_fixed") else parent.get("value_fixed")
        ),
        "has_value_fixed": bool(parent.get("has_value_fixed") or child.get("has_value_fixed")),
        "value_pattern": (
            child.get("value_pattern")
            if child.get("value_pattern") is not None
            else parent.get("value_pattern")
        ),
        "extension_forbidden": bool(
            parent.get("extension_forbidden") or child.get("extension_forbidden")
        ),
        "extension_required": bool(
            parent.get("extension_required") or child.get("extension_required")
        ),
        "slicing_closed": bool(parent.get("slicing_closed") or child.get("slicing_closed")),
        "sub_extensions": merged_subs,
    }


def resolve_all_extensions(
    raw_extensions: dict[str, dict[str, Any]],
    builtin_extensions: Mapping[str, dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    """Resolve baseDefinition inheritance across Extension StructureDefinitions."""
    resolved: dict[str, dict[str, Any]] = {}
    base_ext_url = "http://hl7.org/fhir/StructureDefinition/Extension"

    def _resolve(url: str, seen: set[str]) -> dict[str, Any] | None:
        if url in resolved:
            return resolved[url]
        if url in seen:
            return None
        spec = raw_extensions.get(url)
        if spec is None:
            clean = url.split("|", maxsplit=1)[0]
            if builtin_extensions and clean in builtin_extensions:
                return builtin_extensions[clean]
            return None

        seen.add(url)
        raw_parent = spec.get("base_definition")
        parent_url = raw_parent.split("|", maxsplit=1)[0] if isinstance(raw_parent, str) else None
        parent: dict[str, Any] | None = None
        if parent_url and parent_url != base_ext_url:
            parent = _resolve(parent_url, seen)

        if parent is None:
            resolved[url] = spec
            return spec

        merged = {
            "url": spec["url"],
            "base_definition": spec.get("base_definition"),
            "is_modifier": bool(spec.get("is_modifier") or parent.get("is_modifier")),
            "contexts": spec.get("contexts") or parent.get("contexts") or [],
            "node": _merge_node_specs(parent["node"], spec["node"]),
        }
        resolved[url] = merged
        return merged

    for ext_url in raw_extensions:
        _resolve(ext_url, set())
    return resolved
