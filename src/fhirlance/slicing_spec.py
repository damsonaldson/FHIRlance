"""Pure stdlib extractor and merger for FHIR R4 StructureDefinition slicing specs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, TypeGuard

_VALID_RULES = frozenset({"open", "closed", "openAtEnd"})


@dataclass(slots=True)
class _GroupNode:
    path: str
    rules: str = "open"
    ordered: bool = False
    discriminators: list[dict[str, str]] = field(default_factory=list)
    slices: dict[str, _SliceNode] = field(default_factory=dict)


@dataclass(slots=True)
class _SliceNode:
    slice_name: str
    min: int = 0
    max: str | None = None
    matchers: dict[str, tuple[str, Any]] = field(default_factory=dict)
    type_constraints: dict[str, list[str]] = field(default_factory=dict)
    profile_constraints: dict[str, list[str]] = field(default_factory=dict)
    exists_constraints: dict[str, bool] = field(default_factory=dict)
    sub_groups: dict[str, _GroupNode] = field(default_factory=dict)


def _is_int(value: Any) -> TypeGuard[int]:
    return isinstance(value, int) and not isinstance(value, bool)


def _apply_slicing_meta(group: _GroupNode, slicing: dict[str, Any]) -> None:
    raw_rules = slicing.get("rules", "open")
    group.rules = raw_rules if raw_rules in _VALID_RULES else "open"
    group.ordered = bool(slicing.get("ordered", False))
    raw_disc = slicing.get("discriminator", [])
    if isinstance(raw_disc, list):
        group.discriminators = [
            {"type": str(d["type"]), "path": str(d.get("path") or "$this")}
            for d in raw_disc
            if isinstance(d, dict) and d.get("type")
        ]


def _walk_to_slice(
    top_groups: dict[str, _GroupNode],
    parts: list[str],
    colon_indices: list[int],
) -> tuple[_SliceNode, int]:
    current_groups = top_groups
    prev_idx = -1
    slice_node: _SliceNode | None = None

    for idx in colon_indices:
        field_name, seg_slice_name = parts[idx].split(":", 1)
        rel_segments = [s.split(":", 1)[0] for s in parts[prev_idx + 1 : idx]]
        rel_segments.append(field_name)
        group_path = ".".join(rel_segments)
        group = current_groups.setdefault(group_path, _GroupNode(path=group_path))
        slice_node = group.slices.setdefault(
            seg_slice_name,
            _SliceNode(slice_name=seg_slice_name),
        )
        current_groups = slice_node.sub_groups
        prev_idx = idx

    if slice_node is None:
        raise ValueError("colon_indices must be non-empty")
    return slice_node, prev_idx


def _extract_matcher(el: dict[str, Any]) -> tuple[str, Any] | None:
    fixed = next((v for k, v in el.items() if k.startswith("fixed")), None)
    pattern = next((v for k, v in el.items() if k.startswith("pattern")), None)
    if pattern is not None:
        return ("pattern", deepcopy(pattern))
    if fixed is not None:
        return ("fixed", deepcopy(fixed))
    return None


def _extract_type_and_profiles(el: dict[str, Any]) -> tuple[list[str], list[str]]:
    raw_types = el.get("type")
    if not isinstance(raw_types, list) or not raw_types:
        return [], []

    type_codes: list[str] = []
    profile_urls: list[str] = []
    for entry in raw_types:
        if not isinstance(entry, dict):
            continue
        code = entry.get("code")
        if isinstance(code, str) and code:
            type_codes.append(code)
        for key in ("profile", "targetProfile"):
            urls = entry.get(key)
            if isinstance(urls, list):
                profile_urls.extend(u for u in urls if isinstance(u, str) and u)

    return type_codes, list(dict.fromkeys(profile_urls))


def _record_slice_constraints(
    slice_node: _SliceNode,
    el: dict[str, Any],
    rel_sub: str,
) -> None:
    el_min = el.get("min")
    el_max = el.get("max")

    if rel_sub == "":
        if _is_int(el_min):
            slice_node.min = el_min
        if el_max is not None:
            slice_node.max = str(el_max)

    matcher = _extract_matcher(el)
    if matcher is not None:
        slice_node.matchers[rel_sub] = matcher

    type_codes, profile_urls = _extract_type_and_profiles(el)
    if type_codes:
        slice_node.type_constraints[rel_sub] = type_codes
    if profile_urls:
        slice_node.profile_constraints[rel_sub] = profile_urls

    if rel_sub:
        if _is_int(el_min) and el_min >= 1:
            slice_node.exists_constraints[rel_sub] = True
        elif el_max == "0":
            slice_node.exists_constraints[rel_sub] = False


def _process_element(el: dict[str, Any], top_groups: dict[str, _GroupNode]) -> None:
    el_id = el.get("id") or el.get("path") or ""
    if not isinstance(el_id, str) or not el_id:
        return

    parts = el_id.split(".")
    colon_indices = [i for i, seg in enumerate(parts) if ":" in seg]
    slicing = el.get("slicing")

    if not colon_indices:
        if isinstance(slicing, dict):
            group = top_groups.setdefault(el_id, _GroupNode(path=el_id))
            _apply_slicing_meta(group, slicing)
        return

    slice_node, last_idx = _walk_to_slice(top_groups, parts, colon_indices)
    rel_sub = "" if last_idx == len(parts) - 1 else ".".join(parts[last_idx + 1 :])

    if rel_sub == "" and isinstance(el.get("sliceName"), str) and el["sliceName"]:
        slice_node.slice_name = el["sliceName"]

    if isinstance(slicing, dict) and rel_sub != "":
        sub_group = slice_node.sub_groups.setdefault(rel_sub, _GroupNode(path=rel_sub))
        _apply_slicing_meta(sub_group, slicing)

    _record_slice_constraints(slice_node, el, rel_sub)


def _serialize_slice(sl: _SliceNode) -> dict[str, Any]:
    sub_groups = [
        sg_dict for sg in sl.sub_groups.values() if (sg_dict := _serialize_group(sg)) is not None
    ]
    return {
        "slice_name": sl.slice_name,
        "min": sl.min,
        "max": sl.max,
        "matchers": dict(sl.matchers),
        "type_constraints": dict(sl.type_constraints),
        "profile_constraints": dict(sl.profile_constraints),
        "exists_constraints": dict(sl.exists_constraints),
        "sub_groups": sub_groups,
    }


def _is_significant_slice(sl_dict: dict[str, Any]) -> bool:
    if sl_dict["min"] >= 1:
        return True
    max_val = sl_dict["max"]
    if max_val is not None and max_val != "*":
        return True
    return bool(
        sl_dict["matchers"]
        or sl_dict["type_constraints"]
        or sl_dict["profile_constraints"]
        or sl_dict["exists_constraints"]
        or sl_dict["sub_groups"]
    )


def _serialize_group(group: _GroupNode) -> dict[str, Any] | None:
    slices = [_serialize_slice(sl) for sl in group.slices.values()]
    keep = (
        group.rules != "open"
        or group.ordered
        or bool(group.discriminators)
        or any(_is_significant_slice(sl) for sl in slices)
    )
    if not keep:
        return None
    return {
        "path": group.path,
        "rules": group.rules,
        "ordered": group.ordered,
        "discriminators": list(group.discriminators),
        "slices": slices,
    }


def extract_slice_groups(elements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract hierarchical slicing specifications from StructureDefinition elements."""
    top_groups: dict[str, _GroupNode] = {}
    for el in elements:
        if isinstance(el, dict):
            _process_element(el, top_groups)

    return [
        group_dict
        for group in top_groups.values()
        if (group_dict := _serialize_group(group)) is not None
    ]


def _merge_slice(parent_sl: dict[str, Any], child_sl: dict[str, Any]) -> dict[str, Any]:
    child_max = child_sl.get("max")
    merged_max = child_max if child_max is not None else parent_sl.get("max")
    return {
        "slice_name": child_sl["slice_name"],
        "min": max(int(parent_sl.get("min", 0)), int(child_sl.get("min", 0))),
        "max": merged_max,
        "matchers": {
            **deepcopy(parent_sl.get("matchers", {})),
            **deepcopy(child_sl.get("matchers", {})),
        },
        "type_constraints": {
            **deepcopy(parent_sl.get("type_constraints", {})),
            **deepcopy(child_sl.get("type_constraints", {})),
        },
        "profile_constraints": {
            **deepcopy(parent_sl.get("profile_constraints", {})),
            **deepcopy(child_sl.get("profile_constraints", {})),
        },
        "exists_constraints": {
            **parent_sl.get("exists_constraints", {}),
            **child_sl.get("exists_constraints", {}),
        },
        "sub_groups": merge_slice_groups(
            parent_sl.get("sub_groups", []),
            child_sl.get("sub_groups", []),
        ),
    }


def _merge_group(parent_g: dict[str, Any], child_g: dict[str, Any]) -> dict[str, Any]:
    child_rules = child_g.get("rules", "open")
    rules = child_rules if child_rules != "open" else parent_g.get("rules", "open")
    ordered = bool(parent_g.get("ordered", False)) or bool(child_g.get("ordered", False))
    child_disc = child_g.get("discriminators", [])
    discriminators = (
        deepcopy(child_disc) if child_disc else deepcopy(parent_g.get("discriminators", []))
    )

    slices_by_name: dict[str, dict[str, Any]] = {
        sl["slice_name"]: deepcopy(sl) for sl in parent_g.get("slices", [])
    }
    for child_sl in child_g.get("slices", []):
        name = child_sl["slice_name"]
        if name in slices_by_name:
            slices_by_name[name] = _merge_slice(slices_by_name[name], child_sl)
        else:
            slices_by_name[name] = deepcopy(child_sl)

    return {
        "path": child_g["path"],
        "rules": rules,
        "ordered": ordered,
        "discriminators": discriminators,
        "slices": list(slices_by_name.values()),
    }


def merge_slice_groups(
    parent_groups: list[dict[str, Any]],
    child_groups: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Deep-merge parent and child slice groups by path and slice_name."""
    groups_by_path: dict[str, dict[str, Any]] = {g["path"]: deepcopy(g) for g in parent_groups}
    for child_g in child_groups:
        path = child_g["path"]
        if path in groups_by_path:
            groups_by_path[path] = _merge_group(groups_by_path[path], child_g)
        else:
            groups_by_path[path] = deepcopy(child_g)

    return list(groups_by_path.values())
