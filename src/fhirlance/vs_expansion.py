"""Shared ValueSet expansion, CodeSystem hierarchy, and filter evaluation."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

_MAX_HIERARCHY_DEPTH = 64
_MAX_REGEX_LENGTH = 256
_MISSING = object()


@dataclass(frozen=True, slots=True)
class CodeSystemHierarchy:
    """Complete CodeSystem codes, hierarchy, and concept property values."""

    codes: frozenset[str]
    descendants: dict[str, frozenset[str]]
    children: dict[str, frozenset[str]]
    ancestors: dict[str, frozenset[str]]
    property_values: dict[str, dict[str, Any]]


def _extract_property_value(entry: dict[str, Any]) -> Any:
    for key, val in entry.items():
        if not key.startswith("value") or val is None:
            continue
        if key == "valueCoding" and isinstance(val, dict):
            coding_code = val.get("code")
            return coding_code if isinstance(coding_code, str) else val
        return val
    return _MISSING


def _extract_concept_props(item: dict[str, Any]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    if "inactive" in item and item["inactive"] is not None:
        props["inactive"] = item["inactive"]
    raw_props = item.get("property")
    if not isinstance(raw_props, list):
        return props
    for entry in raw_props:
        if not isinstance(entry, dict):
            continue
        prop_code = entry.get("code")
        if not isinstance(prop_code, str) or not prop_code:
            continue
        val = _extract_property_value(entry)
        if val is not _MISSING:
            props[prop_code] = val
    return props


def _record_hierarchy_links(
    code: str,
    parent_code: str | None,
    anc_tuple: tuple[str, ...],
    links: tuple[dict[str, set[str]], dict[str, set[str]], dict[str, set[str]]],
) -> None:
    children_mut, descendants_mut, ancestors_mut = links
    if parent_code is not None:
        children_mut.setdefault(parent_code, set()).add(code)
    if anc_tuple:
        ancestors_mut.setdefault(code, set()).update(anc_tuple)
        for anc in anc_tuple:
            descendants_mut.setdefault(anc, set()).add(code)


def build_code_system_hierarchy(concepts: Sequence[Any]) -> CodeSystemHierarchy:
    """Build a CodeSystemHierarchy iteratively from a CodeSystem concept tree."""
    all_codes: set[str] = set()
    children_mut: dict[str, set[str]] = {}
    descendants_mut: dict[str, set[str]] = {}
    ancestors_mut: dict[str, set[str]] = {}
    property_values: dict[str, dict[str, Any]] = {}
    links = (children_mut, descendants_mut, ancestors_mut)
    stack: list[tuple[Sequence[Any], str | None, tuple[str, ...]]] = [(concepts, None, ())]

    while stack:
        items, parent_code, anc_tuple = stack.pop()
        if len(anc_tuple) >= _MAX_HIERARCHY_DEPTH:
            continue
        for item in items:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            if not isinstance(code, str) or not code:
                continue
            all_codes.add(code)
            _record_hierarchy_links(code, parent_code, anc_tuple, links)
            props = _extract_concept_props(item)
            if props:
                property_values.setdefault(code, {}).update(props)
            sub = item.get("concept")
            if isinstance(sub, list) and sub:
                stack.append((sub, code, (*anc_tuple, code)))

    return CodeSystemHierarchy(
        codes=frozenset(all_codes),
        descendants={k: frozenset(v) for k, v in descendants_mut.items()},
        children={k: frozenset(v) for k, v in children_mut.items()},
        ancestors={k: frozenset(v) for k, v in ancestors_mut.items()},
        property_values=property_values,
    )


def _merge_set_dicts(
    base: Mapping[str, frozenset[str]],
    extra: Mapping[str, frozenset[str]],
) -> dict[str, frozenset[str]]:
    merged = dict(base)
    for key, vals in extra.items():
        merged[key] = (merged[key] | vals) if key in merged else vals
    return merged


def _merge_hierarchies(
    base: CodeSystemHierarchy,
    supplement: CodeSystemHierarchy,
) -> CodeSystemHierarchy:
    merged_props = {k: dict(v) for k, v in base.property_values.items()}
    for code, props in supplement.property_values.items():
        if code in merged_props:
            merged_props[code].update(props)
        else:
            merged_props[code] = dict(props)
    return CodeSystemHierarchy(
        codes=base.codes | supplement.codes,
        descendants=_merge_set_dicts(base.descendants, supplement.descendants),
        children=_merge_set_dicts(base.children, supplement.children),
        ancestors=_merge_set_dicts(base.ancestors, supplement.ancestors),
        property_values=merged_props,
    )


def _split_canonical(raw_url: Any, explicit_version: Any = None) -> tuple[str, str]:
    if not isinstance(raw_url, str) or not raw_url:
        return "", ""
    base, _, embedded_ver = raw_url.partition("|")
    if isinstance(explicit_version, str) and explicit_version:
        return base, explicit_version
    return base, embedded_ver


def _apply_single_supplement(
    sup: dict[str, Any],
    result: dict[str, CodeSystemHierarchy],
) -> None:
    sup_ref = sup.get("supplements")
    concepts = sup.get("concept")
    if not isinstance(sup_ref, str) or not sup_ref or not isinstance(concepts, list):
        return
    base_ref = sup_ref.split("|", 1)[0]
    target_key = sup_ref if sup_ref in result else (base_ref if base_ref in result else "")
    if not target_key:
        return
    old_h = result[target_key]
    merged = _merge_hierarchies(old_h, build_code_system_hierarchy(concepts))
    for key, existing in list(result.items()):
        if existing is old_h:
            result[key] = merged


def merge_code_system_supplements(
    code_systems: Sequence[dict[str, Any]],
) -> dict[str, CodeSystemHierarchy]:
    """Index complete CodeSystems by url and url|version, merging supplements into targets."""
    result: dict[str, CodeSystemHierarchy] = {}
    supplements: list[dict[str, Any]] = []

    for cs in code_systems:
        content = cs.get("content")
        if content == "supplement":
            supplements.append(cs)
            continue
        if content != "complete":
            continue
        url, version = _split_canonical(cs.get("url"), cs.get("version"))
        concepts = cs.get("concept")
        if not url or not isinstance(concepts, list):
            continue
        hierarchy = build_code_system_hierarchy(concepts)
        if not hierarchy.codes:
            continue
        result[url] = hierarchy
        if version:
            result[f"{url}|{version}"] = hierarchy

    for sup in supplements:
        _apply_single_supplement(sup, result)

    return result


def _val_to_str(val: Any) -> str:
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val)


def _eval_exists_filter(hierarchy: CodeSystemHierarchy, prop: str, value: str) -> frozenset[str]:
    lowered = value.lower()
    if lowered == "true":
        return frozenset(c for c in hierarchy.codes if prop in hierarchy.property_values.get(c, {}))
    if lowered == "false":
        return frozenset(
            c for c in hierarchy.codes if prop not in hierarchy.property_values.get(c, {})
        )
    return frozenset()


def _eval_eq_filter(hierarchy: CodeSystemHierarchy, prop: str, value: str) -> frozenset[str]:
    if prop in ("concept", "code", ""):
        return frozenset({value}) if value in hierarchy.codes else frozenset()
    return frozenset(
        c
        for c in hierarchy.codes
        if (pv := hierarchy.property_values.get(c, {}).get(prop)) is not None
        and _val_to_str(pv) == value
    )


def _eval_in_filter(
    hierarchy: CodeSystemHierarchy,
    prop: str,
    value: str,
    *,
    negate: bool,
) -> frozenset[str]:
    targets = set(value.split(","))
    if prop in ("concept", "code", ""):
        return (hierarchy.codes - targets) if negate else (hierarchy.codes & targets)
    matched = {
        c
        for c in hierarchy.codes
        if (pv := hierarchy.property_values.get(c, {}).get(prop)) is not None
        and _val_to_str(pv) in targets
    }
    return (hierarchy.codes - matched) if negate else frozenset(matched)


def _eval_regex_filter(hierarchy: CodeSystemHierarchy, prop: str, value: str) -> frozenset[str]:
    if len(value) > _MAX_REGEX_LENGTH:
        return frozenset()
    try:
        rx = re.compile(value)
    except re.error:
        return frozenset()
    if prop in ("concept", "code", ""):
        return frozenset(c for c in hierarchy.codes if rx.fullmatch(c))
    return frozenset(
        c
        for c in hierarchy.codes
        if (pv := hierarchy.property_values.get(c, {}).get(prop)) is not None
        and rx.fullmatch(_val_to_str(pv))
    )


def _eval_hierarchy_op(
    hierarchy: CodeSystemHierarchy,
    op: str,
    value: str,
) -> frozenset[str]:
    result: frozenset[str] = frozenset()
    if op == "is-a":
        root = frozenset({value}) if value in hierarchy.codes else frozenset()
        result = root | hierarchy.descendants.get(value, frozenset())
    elif op == "descendent-of":
        result = hierarchy.descendants.get(value, frozenset())
    elif op == "is-not-a":
        root = frozenset({value}) if value in hierarchy.codes else frozenset()
        result = hierarchy.codes - (root | hierarchy.descendants.get(value, frozenset()))
    elif op == "child-of":
        result = hierarchy.children.get(value, frozenset())
    elif op == "generalizes" and value in hierarchy.codes:
        result = frozenset({value}) | hierarchy.ancestors.get(value, frozenset())
    return result


def eval_filter(
    hierarchy: CodeSystemHierarchy,
    prop: str,
    op: str,
    value: str,
) -> frozenset[str]:
    """Evaluate a single ValueSet.compose.include.filter against a CodeSystemHierarchy."""
    result: frozenset[str] = frozenset()
    if op in ("is-a", "descendent-of", "is-not-a", "child-of", "generalizes"):
        result = _eval_hierarchy_op(hierarchy, op, value)
    elif op == "exists":
        result = _eval_exists_filter(hierarchy, prop, value)
    elif op == "=":
        result = _eval_eq_filter(hierarchy, prop, value)
    elif op == "in":
        result = _eval_in_filter(hierarchy, prop, value, negate=False)
    elif op == "not-in":
        result = _eval_in_filter(hierarchy, prop, value, negate=True)
    elif op == "regex":
        result = _eval_regex_filter(hierarchy, prop, value)
    return result


def eval_filters(
    filters: Sequence[dict[str, Any]],
    hierarchy: CodeSystemHierarchy,
) -> frozenset[str]:
    """Evaluate a list of ValueSet filters by intersecting their results."""
    matched: frozenset[str] | None = None
    for f in filters:
        prop = str(f.get("property", "concept"))
        op = str(f.get("op", ""))
        val = str(f.get("value", ""))
        curr = eval_filter(hierarchy, prop, op, val)
        matched = curr if matched is None else (matched & curr)
    return matched if matched is not None else frozenset()


def _lookup_hierarchy(
    hierarchies: Mapping[str, CodeSystemHierarchy],
    sys_url: str,
    sys_ver: str,
) -> CodeSystemHierarchy | None:
    if sys_url and sys_ver:
        versioned = hierarchies.get(f"{sys_url}|{sys_ver}")
        if versioned is not None:
            return versioned
    return hierarchies.get(sys_url) if sys_url else None


def _collect_expansion_contains(
    contains: Sequence[Any],
    codes: set[str],
    systems: set[str],
) -> None:
    stack: list[Sequence[Any]] = [contains]
    while stack:
        items = stack.pop()
        for item in items:
            if not isinstance(item, dict):
                continue
            code = item.get("code")
            sys_url, _ = _split_canonical(item.get("system"))
            if isinstance(code, str) and code:
                codes.add(code)
            if sys_url:
                systems.add(sys_url)
            sub = item.get("contains")
            if isinstance(sub, list) and sub:
                stack.append(sub)


@dataclass(slots=True)
class _ExpansionState:
    sys_codes: dict[str, set[str]]
    untracked: set[str]
    systems: set[str]
    complete: bool = True

    def add_codes(self, sys_url: str, new_codes: frozenset[str] | set[str]) -> None:
        if sys_url:
            self.sys_codes.setdefault(sys_url, set()).update(new_codes)
        else:
            self.untracked.update(new_codes)

    def remove_codes(self, sys_url: str, drop_codes: frozenset[str] | set[str]) -> None:
        if sys_url:
            if sys_url in self.sys_codes:
                self.sys_codes[sys_url].difference_update(drop_codes)
            return
        for sc in self.sys_codes.values():
            sc.difference_update(drop_codes)
        self.untracked.difference_update(drop_codes)


def _lookup_resolved_vs(
    resolved_vs: Mapping[str, frozenset[str]] | None,
    ref: Any,
) -> frozenset[str] | None:
    if resolved_vs is None:
        return None
    ref_str = str(ref)
    imported = resolved_vs.get(ref_str)
    if imported is None:
        imported = resolved_vs.get(ref_str.split("|", 1)[0])
    return imported


def _apply_imported_vs_refs(
    raw_refs: Any,
    resolved_vs: Mapping[str, frozenset[str]] | None,
    state: _ExpansionState,
) -> None:
    if not raw_refs:
        return
    refs = raw_refs if isinstance(raw_refs, list) else [raw_refs]
    for ref in refs:
        imported = _lookup_resolved_vs(resolved_vs, ref)
        if imported is not None:
            state.untracked.update(imported)
        else:
            state.complete = False


def _apply_include_entry(
    inc: dict[str, Any],
    hierarchies: Mapping[str, CodeSystemHierarchy],
    resolved_vs: Mapping[str, frozenset[str]] | None,
    state: _ExpansionState,
) -> None:
    sys_url, sys_ver = _split_canonical(inc.get("system"), inc.get("version"))
    if sys_url:
        state.systems.add(sys_url)
    if "concept" in inc:
        concepts = {
            c["code"]
            for c in inc.get("concept", [])
            if isinstance(c, dict) and isinstance(c.get("code"), str) and c["code"]
        }
        state.add_codes(sys_url, concepts)
    elif "filter" in inc:
        cs_hier = _lookup_hierarchy(hierarchies, sys_url, sys_ver)
        if cs_hier is not None:
            state.add_codes(sys_url, eval_filters(inc["filter"], cs_hier))
        else:
            state.complete = False
    elif sys_url:
        cs_hier = _lookup_hierarchy(hierarchies, sys_url, sys_ver)
        if cs_hier is not None:
            state.add_codes(sys_url, cs_hier.codes)
        else:
            state.complete = False

    _apply_imported_vs_refs(inc.get("valueSet"), resolved_vs, state)


def _apply_exclude_entry(
    exc: dict[str, Any],
    hierarchies: Mapping[str, CodeSystemHierarchy],
    resolved_vs: Mapping[str, frozenset[str]] | None,
    state: _ExpansionState,
) -> None:
    sys_url, sys_ver = _split_canonical(exc.get("system"), exc.get("version"))
    if "concept" in exc:
        drop = {
            c["code"]
            for c in exc.get("concept", [])
            if isinstance(c, dict) and isinstance(c.get("code"), str) and c["code"]
        }
        state.remove_codes(sys_url, drop)
    elif "filter" in exc:
        cs_hier = _lookup_hierarchy(hierarchies, sys_url, sys_ver)
        if cs_hier is not None:
            state.remove_codes(sys_url, eval_filters(exc["filter"], cs_hier))
    elif sys_url and "valueSet" not in exc:
        state.sys_codes.pop(sys_url, None)

    raw_refs = exc.get("valueSet")
    if not raw_refs:
        return
    refs = raw_refs if isinstance(raw_refs, list) else [raw_refs]
    for ref in refs:
        imported = _lookup_resolved_vs(resolved_vs, ref)
        if imported is not None:
            state.remove_codes("", imported)


def _expand_from_contains(vs: dict[str, Any]) -> tuple[frozenset[str], frozenset[str]]:
    contains = (vs.get("expansion") or {}).get("contains") or []
    if not isinstance(contains, list):
        return frozenset(), frozenset()
    codes: set[str] = set()
    systems: set[str] = set()
    _collect_expansion_contains(contains, codes, systems)
    return frozenset(codes), frozenset(systems)


def expand_value_set_codes(
    vs: dict[str, Any],
    hierarchies: Mapping[str, CodeSystemHierarchy],
    resolved_vs: Mapping[str, frozenset[str]] | None = None,
) -> tuple[frozenset[str], frozenset[str], bool]:
    """Expand a ValueSet into (codes, systems, complete_flag)."""
    compose = vs.get("compose")
    if not isinstance(compose, dict):
        exp_codes, exp_systems = _expand_from_contains(vs)
        return exp_codes, exp_systems, True

    state = _ExpansionState(sys_codes={}, untracked=set(), systems=set())
    for inc in compose.get("include") or []:
        if isinstance(inc, dict):
            _apply_include_entry(inc, hierarchies, resolved_vs, state)
    for exc in compose.get("exclude") or []:
        if isinstance(exc, dict):
            _apply_exclude_entry(exc, hierarchies, resolved_vs, state)

    all_codes = frozenset(state.untracked).union(*state.sys_codes.values())
    all_systems = frozenset(state.systems)
    if not all_codes:
        exp_codes, exp_systems = _expand_from_contains(vs)
        if exp_codes:
            return exp_codes, all_systems | exp_systems, True
    return all_codes, all_systems, state.complete
