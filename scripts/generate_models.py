"""Generate Pydantic v2 models for all FHIR R4 complex types, 146 resources, and IG profiles."""

from __future__ import annotations

import json
import keyword
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from fhirlance.extension_spec import extract_extension_spec, resolve_all_extensions
from fhirlance.slicing_spec import extract_slice_groups, merge_slice_groups

R4_PKG = Path.home() / ".fhir" / "packages" / "hl7.fhir.r4.core#4.0.1" / "package"
THO_PKG = Path.home() / ".fhir" / "packages" / "hl7.terminology.r4#6.2.0" / "package"
IG_PKGS = [
    R4_PKG,
    Path.home() / ".fhir" / "packages" / "hl7.fhir.ca.baseline#1.2.0" / "package",
    Path.home() / ".fhir" / "packages" / "ca.infoway.io.core#1.1.0-dft-preballot" / "package",
    Path.home() / ".fhir" / "packages" / "hl7.fhir.uv.ips#1.0.0" / "package",
    Path.home() / ".fhir" / "packages" / "hl7.fhir.us.core.r4#8.0.1" / "package",
]
TERMINOLOGY_PKGS = [*IG_PKGS, THO_PKG]
OUT_DIR = Path(__file__).resolve().parents[1] / "src" / "fhirlance"

PYTHON_KEYWORDS = set(keyword.kwlist) | {"None", "True", "False"}
_MAX_LITERAL_CODES = 60
_MAX_SNAPSHOT_TYPE_NARROWING = 4
_CHOICE_SUFFIX = "[x]"
_CHOICE_SUFFIX_LEN = len(_CHOICE_SUFFIX)

PRIMITIVE_MAP: dict[str, str] = {
    "boolean": "StrictBool",
    "integer": "FHIRInteger",
    "decimal": "FHIRDecimal",
    "date": "FHIRDate",
    "dateTime": "FHIRDateTime",
    "instant": "FHIRInstant",
    "time": "FHIRTime",
    "id": "FHIRId",
    "code": "FHIRCode",
    "positiveInt": "FHIRPositiveInt",
    "unsignedInt": "FHIRUnsignedInt",
    "string": "StrictStr",
    "uri": "StrictStr",
    "url": "StrictStr",
    "canonical": "StrictStr",
    "oid": "StrictStr",
    "uuid": "StrictStr",
    "markdown": "StrictStr",
    "base64Binary": "StrictStr",
    "xhtml": "StrictStr",
    "http://hl7.org/fhirpath/System.String": "StrictStr",
}

DOMAIN_BASE_FIELDS = frozenset(
    {
        "id",
        "meta",
        "implicitRules",
        "language",
        "text",
        "contained",
        "extension",
        "modifierExtension",
    }
)


def _glob_json(pkg: Path, prefix: str) -> list[Path]:
    """Glob JSON files matching prefix case-insensitively for Linux filesystem compatibility."""
    prefix_lower = prefix.lower()
    return sorted(p for p in pkg.glob("*.json") if p.name.lower().startswith(prefix_lower))


@dataclass(frozen=True, slots=True)
class CodegenContext:
    """Shared context for emitting Pydantic model classes from StructureDefinitions."""

    root_name: str
    by_parent: dict[str, list[dict[str, Any]]]
    value_sets: dict[str, list[str]]
    known_types: set[str]
    is_resource_pkg: bool


@dataclass(frozen=True, slots=True)
class CodeSystemHierarchy:
    """Complete CodeSystem codes and descendant hierarchy for filter expansion."""

    codes: frozenset[str]
    descendants: dict[str, frozenset[str]]


@dataclass(frozen=True, slots=True)
class ValueSetSpec:
    """Expanded ValueSet specification with local codes and external system tracking."""

    codes: list[str]
    system_codes: dict[str, list[str]]
    external_systems: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "codes": self.codes,
            "system_codes": self.system_codes,
            "external_systems": self.external_systems,
        }


@dataclass(slots=True)
class _VsTarget:
    codes: set[str] = field(default_factory=set)
    sys_codes: dict[str, set[str]] = field(default_factory=dict)
    ext_systems: set[str] = field(default_factory=set)


@dataclass(frozen=True, slots=True)
class _VsResolverContext:
    raw_vs: dict[str, dict[str, Any]]
    complete_cs: dict[str, list[str]]
    hierarchy_map: dict[str, CodeSystemHierarchy]
    resolved: dict[str, ValueSetSpec]
    resolving: set[str]


@dataclass(slots=True)
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


def _safe_field_name(name: str) -> tuple[str, str | None]:
    if name in PYTHON_KEYWORDS or name.startswith("_"):
        return f"{name}_", name
    return name, None


def _pascal_from_path(path: str) -> str:
    return "".join(part[0].upper() + part[1:] for part in path.split("."))


def _walk_concept_tree(
    concepts: list[dict[str, Any]],
    all_codes: set[str],
    descendants: dict[str, set[str]],
) -> set[str]:
    subtree: set[str] = set()
    for item in concepts:
        code = item.get("code")
        if not code or not isinstance(code, str):
            continue
        all_codes.add(code)
        subtree.add(code)
        sub_concepts = item.get("concept")
        children: set[str] = set()
        if isinstance(sub_concepts, list):
            children = _walk_concept_tree(sub_concepts, all_codes, descendants)
        descendants.setdefault(code, set()).update(children)
        subtree.update(children)
    return subtree


def _load_complete_code_systems(
    ig_pkgs: list[Path],
) -> tuple[dict[str, list[str]], dict[str, CodeSystemHierarchy]]:
    """Extract complete CodeSystems and their hierarchies across all IG packages."""
    complete_map: dict[str, list[str]] = {}
    hierarchy_map: dict[str, CodeSystemHierarchy] = {}
    for pkg in ig_pkgs:
        if not pkg.exists():
            continue
        for path in _glob_json(pkg, "CodeSystem-"):
            cs = json.loads(path.read_text(encoding="utf-8"))
            url = (cs.get("url") or "").split("|", 1)[0]
            if not url or cs.get("content") != "complete":
                continue
            all_codes: set[str] = set()
            descendants: dict[str, set[str]] = {}
            _walk_concept_tree(cs.get("concept", []), all_codes, descendants)
            if not all_codes:
                continue
            complete_map[url] = sorted(all_codes)
            hierarchy_map[url] = CodeSystemHierarchy(
                codes=frozenset(all_codes),
                descendants={k: frozenset(v) for k, v in descendants.items()},
            )
    return complete_map, hierarchy_map


def _eval_regex_filter(val: str, codes: frozenset[str]) -> set[str]:
    try:
        rx = re.compile(val)
        return {c for c in codes if rx.fullmatch(c)}
    except re.error:
        return set()


def _eval_single_filter(
    f: dict[str, Any],
    cs: CodeSystemHierarchy,
) -> set[str]:
    op = f.get("op")
    val = str(f.get("value", ""))
    if op == "is-a":
        return ({val} if val in cs.codes else set()) | set(cs.descendants.get(val, ()))
    if op == "descendent-of":
        return set(cs.descendants.get(val, ()))
    if op == "=":
        return {val} if val in cs.codes else set()
    if op == "in":
        return set(val.split(",")) & cs.codes
    if op == "regex":
        return _eval_regex_filter(val, cs.codes)
    not_allowed = ({val} if val in cs.codes else set()) | set(cs.descendants.get(val, ()))
    return set(cs.codes - not_allowed) if op == "is-not-a" else set()


def _eval_filters(
    filters: list[dict[str, Any]],
    cs: CodeSystemHierarchy,
) -> set[str]:
    matches: set[str] | None = None
    for f in filters:
        m = _eval_single_filter(f, cs)
        matches = m if matches is None else (matches & m)
    return matches or set()


def _collect_expansion_contains(
    contains: list[Any],
    sys_codes: dict[str, set[str]],
    codes: set[str],
) -> None:
    for item in contains:
        if not isinstance(item, dict):
            continue
        code = item.get("code")
        sys_url = (item.get("system") or "").split("|", 1)[0]
        if code and isinstance(code, str):
            codes.add(code)
            if sys_url:
                sys_codes.setdefault(sys_url, set()).add(code)
        sub_contains = item.get("contains")
        if isinstance(sub_contains, list):
            _collect_expansion_contains(sub_contains, sys_codes, codes)


def _apply_imported_valuesets(
    ctx: _VsResolverContext,
    raw_refs: Any,
    target: _VsTarget,
) -> None:
    if not raw_refs:
        return
    refs = raw_refs if isinstance(raw_refs, list) else [raw_refs]
    for ref_vs in refs:
        ref_url = str(ref_vs).split("|", 1)[0]
        ref_spec = _resolve_single_value_set(ctx, ref_url)
        target.codes.update(ref_spec.codes)
        for s, sc in ref_spec.system_codes.items():
            target.sys_codes.setdefault(s, set()).update(sc)
        target.ext_systems.update(ref_spec.external_systems)


def _apply_include_concepts(
    inc: dict[str, Any],
    sys_url: str,
    target: _VsTarget,
) -> None:
    for c in inc.get("concept", []):
        code = c.get("code")
        if code and isinstance(code, str):
            target.codes.add(code)
            if sys_url:
                target.sys_codes.setdefault(sys_url, set()).add(code)


def _apply_include_filter(
    ctx: _VsResolverContext,
    inc: dict[str, Any],
    sys_url: str,
    target: _VsTarget,
) -> None:
    if sys_url in ctx.hierarchy_map:
        matched = _eval_filters(inc["filter"], ctx.hierarchy_map[sys_url])
        target.codes.update(matched)
        if matched and sys_url:
            target.sys_codes.setdefault(sys_url, set()).update(matched)
    elif sys_url:
        target.ext_systems.add(sys_url)


def _apply_include_system(
    ctx: _VsResolverContext,
    sys_url: str,
    target: _VsTarget,
) -> None:
    if sys_url in ctx.complete_cs:
        matched = set(ctx.complete_cs[sys_url])
        target.codes.update(matched)
        target.sys_codes.setdefault(sys_url, set()).update(matched)
    elif sys_url:
        target.ext_systems.add(sys_url)


def _apply_include(
    ctx: _VsResolverContext,
    inc: dict[str, Any],
    target: _VsTarget,
) -> None:
    sys_url = (inc.get("system") or "").split("|", 1)[0]
    if "concept" in inc:
        _apply_include_concepts(inc, sys_url, target)
    elif "filter" in inc:
        _apply_include_filter(ctx, inc, sys_url, target)
    elif sys_url:
        _apply_include_system(ctx, sys_url, target)

    _apply_imported_valuesets(ctx, inc.get("valueSet"), target)


def _apply_exclude_concepts(
    exc: dict[str, Any],
    sys_url: str,
    target: _VsTarget,
) -> None:
    for c in exc.get("concept", []):
        code = c.get("code")
        if not code or not isinstance(code, str):
            continue
        if sys_url in target.sys_codes:
            target.sys_codes[sys_url].discard(code)
        elif not sys_url:
            for s in target.sys_codes:
                target.sys_codes[s].discard(code)


def _apply_exclude_filter(
    ctx: _VsResolverContext,
    exc: dict[str, Any],
    sys_url: str,
    target: _VsTarget,
) -> None:
    if sys_url in ctx.hierarchy_map:
        excluded = _eval_filters(exc["filter"], ctx.hierarchy_map[sys_url])
        if sys_url in target.sys_codes:
            target.sys_codes[sys_url].difference_update(excluded)


def _apply_exclude(
    ctx: _VsResolverContext,
    exc: dict[str, Any],
    target: _VsTarget,
) -> None:
    sys_url = (exc.get("system") or "").split("|", 1)[0]
    if "concept" in exc:
        _apply_exclude_concepts(exc, sys_url, target)
    elif "filter" in exc:
        _apply_exclude_filter(ctx, exc, sys_url, target)
    elif sys_url:
        target.sys_codes.pop(sys_url, None)


def _resolve_single_value_set(
    ctx: _VsResolverContext,
    url: str,
) -> ValueSetSpec:
    if url in ctx.resolved:
        return ctx.resolved[url]
    if url in ctx.resolving:
        return ValueSetSpec(codes=[], system_codes={}, external_systems=[])
    raw = ctx.raw_vs.get(url)
    if raw is None:
        return ValueSetSpec(codes=[], system_codes={}, external_systems=["*"])

    ctx.resolving.add(url)
    target = _VsTarget()
    compose = raw.get("compose")
    if not compose:
        contains = raw.get("expansion", {}).get("contains", [])
        if isinstance(contains, list):
            _collect_expansion_contains(contains, target.sys_codes, target.codes)
    else:
        for inc in compose.get("include", []):
            _apply_include(ctx, inc, target)
        for exc in compose.get("exclude", []):
            _apply_exclude(ctx, exc, target)
        clean_sys = {s: sorted(sc) for s, sc in sorted(target.sys_codes.items()) if sc}
        target.codes = set().union(*clean_sys.values()) if clean_sys else target.codes

    ctx.resolving.remove(url)
    spec = ValueSetSpec(
        codes=sorted(target.codes),
        system_codes={s: sorted(sc) for s, sc in sorted(target.sys_codes.items()) if sc},
        external_systems=sorted(target.ext_systems),
    )
    ctx.resolved[url] = spec
    return spec


def _load_all_value_sets(
    ig_pkgs: list[Path],
    complete_cs: dict[str, list[str]],
    hierarchy_map: dict[str, CodeSystemHierarchy],
) -> dict[str, ValueSetSpec]:
    """Load and resolve all ValueSets across all IG packages."""
    raw_vs: dict[str, dict[str, Any]] = {}
    for pkg in ig_pkgs:
        if not pkg.exists():
            continue
        for path in _glob_json(pkg, "ValueSet-"):
            vs = json.loads(path.read_text(encoding="utf-8"))
            url = (vs.get("url") or "").split("|", 1)[0]
            if url:
                raw_vs[url] = vs

    ctx = _VsResolverContext(
        raw_vs=raw_vs,
        complete_cs=complete_cs,
        hierarchy_map=hierarchy_map,
        resolved={},
        resolving=set(),
    )
    for u in raw_vs:
        _resolve_single_value_set(ctx, u)
    return ctx.resolved


def _load_terminology(pkg_dir: Path) -> dict[str, list[str]]:
    """Build ValueSet URL -> sorted list of valid codes for a single package."""
    complete_cs, hierarchy_map = _load_complete_code_systems([pkg_dir])
    specs = _load_all_value_sets([pkg_dir], complete_cs, hierarchy_map)
    return {u: s.codes for u, s in specs.items()}


def _resolve_code_literal(elem: dict[str, Any], value_sets: dict[str, list[str]]) -> str | None:
    binding = elem.get("binding", {})
    if binding.get("strength") != "required" or not binding.get("valueSet"):
        return None
    vs_url = binding["valueSet"].split("|")[0]
    codes = value_sets.get(vs_url)
    if not codes or len(codes) > _MAX_LITERAL_CODES:
        return None
    literals = ", ".join(repr(c) for c in codes)
    return f"Literal[{literals}]"


def _resolve_type_expr(
    elem: dict[str, Any],
    backbone_name: str | None,
    ctx: CodegenContext,
) -> str:
    if backbone_name:
        return backbone_name

    content_ref = elem.get("contentReference")
    if isinstance(content_ref, str) and content_ref.startswith("#"):
        return _pascal_from_path(content_ref[1:])

    types = elem.get("type", [])
    code = types[0].get("code", "Any") if types else "Any"
    if code in PRIMITIVE_MAP:
        literal = _resolve_code_literal(elem, ctx.value_sets) if code == "code" else None
        return literal if literal is not None else PRIMITIVE_MAP[code]

    if code in ("Resource", "DomainResource"):
        return "dict[str, Any]"
    if code in ctx.known_types:
        return f"fhir_types.{code}" if ctx.is_resource_pkg else code
    return "Any"


def _format_field_line(
    py_name: str,
    alias: str | None,
    type_expr: str,
    *,
    is_list: bool,
    is_required: bool,
) -> str:
    ann = f"Annotated[list[{type_expr}], Field(min_length=1)]" if is_list else type_expr
    if is_required:
        if alias:
            return f"    {py_name}: {ann} = Field(alias={alias!r})"
        return f"    {py_name}: {ann}"
    if alias:
        return f"    {py_name}: {ann} | None = Field(default=None, alias={alias!r})"
    return f"    {py_name}: {ann} | None = None"


def _build_choice_fields(
    elem: dict[str, Any],
    raw_name: str,
    ctx: CodegenContext,
    *,
    is_list: bool,
) -> tuple[list[str], list[str]]:
    stem = raw_name[:-_CHOICE_SUFFIX_LEN]
    field_lines: list[str] = []
    variant_names: list[str] = []
    for type_entry in elem.get("type", []):
        t_code = type_entry.get("code", "string")
        suffix = t_code[0].upper() + t_code[1:]
        v_py, v_alias = _safe_field_name(f"{stem}{suffix}")
        t_expr = _resolve_type_expr(
            {"type": [type_entry], "binding": elem.get("binding", {})},
            None,
            ctx,
        )
        field_lines.append(
            _format_field_line(v_py, v_alias, t_expr, is_list=is_list, is_required=False)
        )
        variant_names.append(v_py)
    return field_lines, variant_names


def _build_choice_validator_lines(
    class_name: str,
    choice_groups: list[tuple[str, list[str], bool]],
) -> list[str]:
    lines = [
        "",
        "    @model_validator(mode='after')",
        f"    def _check_choices(self) -> {class_name!r}:",
    ]
    for raw_name, variants, is_req in choice_groups:
        v_tuple = ", ".join(repr(v) for v in variants)
        lines.append(
            f"        _present = sum(1 for _f in ({v_tuple},) if getattr(self, _f) is not None)"
        )
        msg = (
            f"'{raw_name} requires exactly one value'"
            if is_req
            else f"'{raw_name} allows at most one value'"
        )
        cond = "_present != 1" if is_req else "_present > 1"
        lines.append(f"        if {cond}: raise ValueError({msg})")
    lines.append("        return self")
    return lines


def _resolve_base_class(
    class_name: str,
    children: list[dict[str, Any]],
    ctx: CodegenContext,
    *,
    is_root: bool,
) -> str:
    if is_root and ctx.is_resource_pkg:
        has_meta = any(c["path"].endswith(".meta") for c in children)
        return "DomainResourceR4" if has_meta else "FHIRBaseModel"
    if class_name == "Extension":
        return "ExtensionBase"
    return "FHIRBaseModel"


def _emit_class(
    path: str,
    class_name: str,
    ctx: CodegenContext,
    emitted: list[str],
    *,
    is_root: bool,
) -> None:
    children = ctx.by_parent.get(path, [])
    backbone_children: dict[str, str] = {}
    for ch in children:
        ch_path = ch["path"]
        ch_types = [t.get("code") for t in ch.get("type", [])]
        if ch_path in ctx.by_parent and any(t in ("BackboneElement", "Element") for t in ch_types):
            sub_cls = _pascal_from_path(ch_path)
            backbone_children[ch_path] = sub_cls
            _emit_class(ch_path, sub_cls, ctx, emitted, is_root=False)

    base = _resolve_base_class(class_name, children, ctx, is_root=is_root)
    lines = [f"class {class_name}({base}):"]
    field_lines: list[str] = []
    choice_groups: list[tuple[str, list[str], bool]] = []

    if is_root and ctx.is_resource_pkg:
        field_lines.append(f"    resourceType: Literal[{ctx.root_name!r}]")

    for ch in children:
        ch_path = ch["path"]
        raw_name = ch_path.rsplit(".", 1)[1]
        if is_root and base == "DomainResourceR4" and raw_name in DOMAIN_BASE_FIELDS:
            continue

        is_list = ch.get("max") == "*"
        is_req = ch.get("min", 0) >= 1
        if raw_name.endswith(_CHOICE_SUFFIX):
            c_fields, variants = _build_choice_fields(ch, raw_name, ctx, is_list=is_list)
            field_lines.extend(c_fields)
            choice_groups.append((raw_name, variants, is_req))
            continue

        py_name, alias = _safe_field_name(raw_name)
        t_expr = _resolve_type_expr(ch, backbone_children.get(ch_path), ctx)
        field_lines.append(
            _format_field_line(py_name, alias, t_expr, is_list=is_list, is_required=is_req)
        )

    if not field_lines and not choice_groups:
        lines.append("    pass")
    else:
        lines.extend(field_lines)
        if choice_groups:
            lines.extend(_build_choice_validator_lines(class_name, choice_groups))
    emitted.append("\n".join(lines))


def _build_models_from_sd(
    sd: dict[str, Any],
    value_sets: dict[str, list[str]],
    known_types: set[str],
    *,
    is_resource_pkg: bool,
) -> tuple[list[str], str]:
    """Generate BackboneElement helper classes + main class for one StructureDefinition."""
    root_name = sd["id"]
    elements = sd.get("snapshot", {}).get("element", [])
    by_parent: dict[str, list[dict[str, Any]]] = {}
    for elem in elements[1:]:
        parent = elem["path"].rsplit(".", 1)[0]
        by_parent.setdefault(parent, []).append(elem)

    ctx = CodegenContext(
        root_name=root_name,
        by_parent=by_parent,
        value_sets=value_sets,
        known_types=known_types,
        is_resource_pkg=is_resource_pkg,
    )
    emitted: list[str] = []
    _emit_class(root_name, root_name, ctx, emitted, is_root=True)
    return emitted, root_name


def _extract_fixed_or_pattern(el: dict[str, Any]) -> tuple[Any | None, Any | None]:
    fixed = next((v for k, v in el.items() if k.startswith("fixed")), None)
    pattern = next((v for k, v in el.items() if k.startswith("pattern")), None)
    return fixed, pattern


def _collect_sd_types(ig_pkgs: list[Path]) -> dict[str, str]:
    sd_type_by_url: dict[str, str] = {}
    for pkg in ig_pkgs:
        if not pkg.exists():
            continue
        for path in _glob_json(pkg, "StructureDefinition-"):
            sd = json.loads(path.read_text(encoding="utf-8"))
            if sd.get("url") and sd.get("type"):
                sd_type_by_url[sd["url"]] = sd["type"]
    return sd_type_by_url


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
    rel_sub = "" if el_id == slice_root_id else ".".join(parts[slice_seg_idx + 1 :])
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
    el_types = el.get("type", [])
    if path.endswith(_CHOICE_SUFFIX) and el_types:
        acc.type_narrowing[path] = [t["code"] for t in el_types if t.get("code")]
    for type_entry in el_types:
        if type_entry.get("code") == "Reference" and type_entry.get("targetProfile"):
            allowed = sorted(
                {
                    sd_type_by_url.get(tp.split("|")[0], tp.rstrip("/").rsplit("/", 1)[-1])
                    for tp in type_entry["targetProfile"]
                }
            )
            if allowed:
                acc.target_types[path] = allowed


def _record_element_binding(
    el: dict[str, Any],
    path: str,
    value_sets: dict[str, list[str]],
    acc: _ProfileAccumulator,
) -> None:
    binding = el.get("binding", {})
    strength = binding.get("strength")
    raw_vs = binding.get("valueSet")
    if strength == "required" and raw_vs:
        vs_url = raw_vs.split("|")[0]
        codes = value_sets.get(vs_url)
        if codes:
            acc.bindings[path] = codes

    if strength in ("required", "extensible") and raw_vs:
        vs_url = raw_vs.split("|")[0]
        rel_path = path.split(".", 1)[1]
        acc.binding_specs[rel_path] = {"strength": strength, "value_set": vs_url}


def _record_differential_element(
    el: dict[str, Any],
    sd_type_by_url: dict[str, str],
    value_sets: dict[str, list[str]],
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
    _record_element_binding(el, path, value_sets, acc)


def _extract_profile_spec(
    sd: dict[str, Any],
    sd_type_by_url: dict[str, str],
    value_sets: dict[str, list[str]],
) -> dict[str, Any]:
    acc = _ProfileAccumulator()
    diff_elements = sd.get("differential", {}).get("element", [])
    for el in diff_elements:
        _record_differential_element(el, sd_type_by_url, value_sets, acc)

    snap_elements = sd.get("snapshot", {}).get("element", [])
    for el in snap_elements:
        sp = el.get("path", "")
        if sp.endswith(_CHOICE_SUFFIX) and ":" not in el.get("id", ""):
            stypes = [t["code"] for t in el.get("type", []) if t.get("code")]
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
        "slice_groups": extract_slice_groups(
            diff_elements if diff_elements else snap_elements,
        ),
    }


def _merge_binding_specs(
    parent_specs: dict[str, dict[str, str]],
    child_specs: dict[str, dict[str, str]],
) -> dict[str, dict[str, str]]:
    """Merge parent and child binding specs, preserving required strength."""
    merged: dict[str, dict[str, str]] = {**parent_specs, **child_specs}
    for path, parent_spec in parent_specs.items():
        if parent_spec.get("strength") == "required" and path in merged:
            merged[path] = {**merged[path], "strength": "required"}
    return merged


def _resolve_all_profiles(profiles: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    resolved: dict[str, dict[str, Any]] = {}

    def _resolve(url: str, seen: set[str]) -> dict[str, Any] | None:
        if url in resolved:
            return resolved[url]
        spec = profiles.get(url)
        if spec is None or url in seen:
            return None
        seen.add(url)
        parent_url = spec.get("base_definition")
        parent = _resolve(parent_url, seen) if parent_url and parent_url in profiles else None
        p_req = set(parent["required"]) if parent else set()
        p_forb = set(parent["forbidden"]) if parent else set()
        p_max1 = set(parent["max_one"]) if parent else set()
        merged: dict[str, Any] = {
            "base_type": spec["base_type"],
            "required": sorted(p_req | set(spec["required"])),
            "forbidden": sorted(p_forb | set(spec["forbidden"])),
            "max_one": sorted(p_max1 | set(spec["max_one"])),
            "fixed": {**(parent["fixed"] if parent else {}), **spec["fixed"]},
            "pattern": {**(parent["pattern"] if parent else {}), **spec["pattern"]},
            "type_narrowing": {
                **(parent["type_narrowing"] if parent else {}),
                **spec["type_narrowing"],
            },
            "target_types": {**(parent["target_types"] if parent else {}), **spec["target_types"]},
            "bindings": {**(parent["bindings"] if parent else {}), **spec["bindings"]},
            "binding_specs": _merge_binding_specs(
                parent.get("binding_specs", {}) if parent else {},
                spec.get("binding_specs", {}),
            ),
            "slices": [*(parent["slices"] if parent else []), *spec["slices"]],
            "slice_groups": merge_slice_groups(
                parent.get("slice_groups", []) if parent else [],
                spec.get("slice_groups", []),
            ),
        }
        resolved[url] = merged
        return merged

    for url in profiles:
        _resolve(url, set())
    return resolved


def _extract_base_resource_bindings(
    r4_pkg: Path,
) -> dict[str, dict[str, dict[str, str]]]:
    """Extract required/extensible bindings for CodeableConcept/Coding elements."""
    bindings: dict[str, dict[str, dict[str, str]]] = {}
    for path in _glob_json(r4_pkg, "StructureDefinition-"):
        sd = json.loads(path.read_text(encoding="utf-8"))
        if (
            sd.get("kind") != "resource"
            or sd.get("abstract")
            or sd.get("derivation") != "specialization"
        ):
            continue
        rtype = sd["id"]
        res_bindings: dict[str, dict[str, str]] = {}
        for el in sd.get("snapshot", {}).get("element", []):
            el_path = el.get("path", "")
            if "." not in el_path:
                continue
            b = el.get("binding")
            if (
                not b
                or b.get("strength") not in ("required", "extensible")
                or not b.get("valueSet")
            ):
                continue
            types = [t.get("code") for t in el.get("type", []) if isinstance(t, dict)]
            if any(t in ("CodeableConcept", "Coding") for t in types):
                rel_path = el_path.split(".", 1)[1]
                vs_url = str(b["valueSet"]).split("|", 1)[0]
                res_bindings[rel_path] = {"strength": b["strength"], "value_set": vs_url}
        bindings[rtype] = res_bindings
    return bindings


def _generate_all_ig_profiles(
    ig_pkgs: list[Path],
    value_sets: dict[str, list[str]],
    complete_cs: dict[str, list[str]] | None = None,
    vs_specs: dict[str, ValueSetSpec] | None = None,
    base_bindings: dict[str, dict[str, dict[str, str]]] | None = None,
) -> str:
    """Extract constraint specs and compile terminology across configured IG packages."""
    sd_type_by_url = _collect_sd_types(ig_pkgs)
    profiles: dict[str, dict[str, Any]] = {}
    extensions: dict[str, dict[str, Any]] = {}
    for pkg in ig_pkgs:
        if not pkg.exists():
            continue
        for path in _glob_json(pkg, "StructureDefinition-"):
            sd = json.loads(path.read_text(encoding="utf-8"))
            url = sd.get("url")
            if not url or sd.get("derivation") != "constraint":
                continue
            if sd.get("type") == "Extension":
                extensions[url] = extract_extension_spec(sd, sd_type_by_url, value_sets)
            elif sd.get("kind") == "resource":
                profiles[url] = _extract_profile_spec(sd, sd_type_by_url, value_sets)

    resolved = _resolve_all_profiles(profiles)
    resolved_extensions = resolve_all_extensions(extensions)
    header = (
        '"""Profile constraints and terminology tables compiled '
        'from R4 Core and IG packages."""\n\n'
        "from typing import Any\n\n"
    )
    cs_table = complete_cs if complete_cs is not None else {}
    vs_table = {u: s.to_dict() for u, s in vs_specs.items()} if vs_specs is not None else {}
    bb_table = base_bindings if base_bindings is not None else {}
    return (
        header
        + f"COMPLETE_CODE_SYSTEMS: dict[str, list[str]] = {cs_table!r}\n\n"
        + f"VALUE_SET_SPECS: dict[str, dict[str, Any]] = {vs_table!r}\n\n"
        + f"BASE_RESOURCE_BINDINGS: dict[str, dict[str, dict[str, str]]] = {bb_table!r}\n\n"
        + f"PROFILE_CONSTRAINTS: dict[str, dict[str, Any]] = {resolved!r}\n\n"
        + f"EXTENSION_CONSTRAINTS: dict[str, dict[str, Any]] = {resolved_extensions!r}\n"
    )


def _write_complex_types(
    complex_sds: list[dict[str, Any]],
    value_sets: dict[str, list[str]],
    known_types: set[str],
) -> None:
    blocks: list[str] = [
        '"""Generated FHIR R4 complex datatypes (39 base types)."""',
        "from __future__ import annotations",
        "from typing import Annotated, Any, Literal",
        "from pydantic import Field, StrictBool, StrictStr, model_validator",
        "from fhirlance.base import (",
        "    ExtensionBase, FHIRBaseModel, FHIRCode, FHIRDate, FHIRDateTime, FHIRDecimal,",
        "    FHIRId, FHIRInstant, FHIRInteger, FHIRPositiveInt, FHIRTime, FHIRUnsignedInt,",
        ")",
        "",
        "class Element(FHIRBaseModel):",
        "    id: StrictStr | None = None",
        "    extension: list[Any] | None = None",
        "",
    ]
    for sd in complex_sds:
        emitted, _ = _build_models_from_sd(sd, value_sets, known_types, is_resource_pkg=False)
        blocks.extend(emitted)
        blocks.append("")
    blocks.extend(f"{sd['id']}.model_rebuild()" for sd in complex_sds)
    (OUT_DIR / "types.py").write_text("\n".join(blocks) + "\n", encoding="utf-8")


def _write_resources(
    resource_sds: list[dict[str, Any]],
    value_sets: dict[str, list[str]],
    known_types: set[str],
) -> list[str]:
    mod_ext = (
        "    modifierExtension: Annotated[list[fhir_types.Extension], Field(min_length=1)] "
        "| None = None"
    )
    blocks: list[str] = [
        '"""Generated FHIR R4 resource models (all 146 base R4 resources)."""',
        "from __future__ import annotations",
        "from typing import Annotated, Any, Literal",
        "from pydantic import Field, StrictBool, StrictStr, model_validator",
        "from fhirlance import types as fhir_types",
        "from fhirlance.base import (",
        "    DomainResourceBase, FHIRBaseModel, FHIRCode, FHIRDate, FHIRDateTime, FHIRDecimal,",
        "    FHIRId, FHIRInstant, FHIRInteger, FHIRPositiveInt, FHIRTime, FHIRUnsignedInt,",
        ")",
        "",
        "class DomainResourceR4(DomainResourceBase):",
        "    meta: fhir_types.Meta | None = None",
        "    text: fhir_types.Narrative | None = None",
        "    contained: Annotated[list[dict[str, Any]], Field(min_length=1)] | None = None",
        "    extension: Annotated[list[fhir_types.Extension], Field(min_length=1)] | None = None",
        mod_ext,
        "",
    ]
    res_names: list[str] = []
    for sd in resource_sds:
        emitted, name = _build_models_from_sd(sd, value_sets, known_types, is_resource_pkg=True)
        blocks.extend(emitted)
        blocks.append("")
        res_names.append(name)

    blocks.append("RESOURCE_MODELS: dict[str, type[FHIRBaseModel]] = {")
    blocks.extend(f"    {name!r}: {name}," for name in res_names)
    blocks.append("}")
    blocks.extend(f"{name}.model_rebuild()" for name in res_names)
    (OUT_DIR / "resources.py").write_text("\n".join(blocks) + "\n", encoding="utf-8")
    return res_names


def main() -> None:
    """Regenerate types.py, resources.py, and profiles.py from cached HL7 FHIR packages."""
    r4_cs, r4_hierarchy = _load_complete_code_systems(IG_PKGS)
    r4_vs_specs = _load_all_value_sets(IG_PKGS, r4_cs, r4_hierarchy)
    r4_vs_codes = {u: s.codes for u, s in r4_vs_specs.items()}

    complete_cs, hierarchy_map = _load_complete_code_systems(TERMINOLOGY_PKGS)
    vs_specs = _load_all_value_sets(TERMINOLOGY_PKGS, complete_cs, hierarchy_map)
    value_set_codes = {u: s.codes for u, s in vs_specs.items()}

    sds = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in _glob_json(R4_PKG, "StructureDefinition-")
    ]
    complex_sds = [
        s
        for s in sds
        if s.get("kind") == "complex-type"
        and not s.get("abstract")
        and s.get("derivation") == "specialization"
    ]
    known_types = {s["id"] for s in complex_sds} | {"Element", "BackboneElement"}
    _write_complex_types(complex_sds, r4_vs_codes, known_types)

    resource_sds = [
        s
        for s in sds
        if s.get("kind") == "resource"
        and not s.get("abstract")
        and s.get("derivation") == "specialization"
    ]
    res_names = _write_resources(resource_sds, r4_vs_codes, known_types)
    base_bindings = _extract_base_resource_bindings(R4_PKG)

    profiles_content = _generate_all_ig_profiles(
        IG_PKGS, value_set_codes, complete_cs, vs_specs, base_bindings
    )
    (OUT_DIR / "profiles.py").write_text(profiles_content, encoding="utf-8")
    print(f"Generated {len(complex_sds)} complex types and {len(res_names)} R4 resources.")
    print(
        f"Compiled {len(complete_cs)} CodeSystems, {len(vs_specs)} ValueSets, "
        f"and {len(base_bindings)} base bindings."
    )


if __name__ == "__main__":
    main()
