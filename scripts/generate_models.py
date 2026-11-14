"""Generate Pydantic v2 models for all FHIR R4 complex types, 146 resources, and IG profiles."""

from __future__ import annotations

import json
import keyword
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

R4_PKG = Path.home() / ".fhir" / "packages" / "hl7.fhir.r4.core#4.0.1" / "package"
IG_PKGS = [
    R4_PKG,
    Path.home() / ".fhir" / "packages" / "hl7.fhir.ca.baseline#1.2.0" / "package",
    Path.home() / ".fhir" / "packages" / "ca.infoway.io.core#1.1.0-dft-preballot" / "package",
    Path.home() / ".fhir" / "packages" / "hl7.fhir.uv.ips#1.0.0" / "package",
    Path.home() / ".fhir" / "packages" / "hl7.fhir.us.core.r4#8.0.1" / "package",
]
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


@dataclass(frozen=True, slots=True)
class CodegenContext:
    """Shared context for emitting Pydantic model classes from StructureDefinitions."""

    root_name: str
    by_parent: dict[str, list[dict[str, Any]]]
    value_sets: dict[str, list[str]]
    known_types: set[str]
    is_resource_pkg: bool


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
    slices: dict[str, dict[str, Any]] = field(default_factory=dict)


def _safe_field_name(name: str) -> tuple[str, str | None]:
    if name in PYTHON_KEYWORDS or name.startswith("_"):
        return f"{name}_", name
    return name, None


def _pascal_from_path(path: str) -> str:
    return "".join(part[0].upper() + part[1:] for part in path.split("."))


def _collect_concepts(concepts: list[dict[str, Any]], out: list[str]) -> None:
    for concept in concepts:
        if "code" in concept:
            out.append(concept["code"])
        if "concept" in concept:
            _collect_concepts(concept["concept"], out)


def _load_code_systems(pkg_dir: Path) -> dict[str, list[str]]:
    code_systems: dict[str, list[str]] = {}
    for path in pkg_dir.glob("CodeSystem-*.json"):
        cs = json.loads(path.read_text(encoding="utf-8"))
        url = cs.get("url")
        if not url:
            continue
        codes: list[str] = []
        _collect_concepts(cs.get("concept", []), codes)
        if codes:
            code_systems[url] = codes
    return code_systems


def _load_terminology(pkg_dir: Path) -> dict[str, list[str]]:
    """Build ValueSet URL -> sorted list of valid codes from CodeSystem & ValueSet JSONs."""
    code_systems = _load_code_systems(pkg_dir)
    value_sets: dict[str, list[str]] = {}
    for path in pkg_dir.glob("ValueSet-*.json"):
        vs = json.loads(path.read_text(encoding="utf-8"))
        url = vs.get("url")
        if not url:
            continue
        codes: list[str] = []
        for inc in vs.get("compose", {}).get("include", []):
            if "concept" in inc:
                codes.extend(c["code"] for c in inc["concept"] if "code" in c)
            elif "system" in inc and not inc.get("filter"):
                codes.extend(code_systems.get(inc["system"], []))
        if codes:
            value_sets[url] = sorted(set(codes))
    return value_sets


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
        for path in pkg.glob("StructureDefinition-*.json"):
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

    binding = el.get("binding", {})
    if binding.get("strength") == "required" and binding.get("valueSet"):
        vs_url = binding["valueSet"].split("|")[0]
        if vs_url in value_sets:
            acc.bindings[path] = value_sets[vs_url]


def _extract_profile_spec(
    sd: dict[str, Any],
    sd_type_by_url: dict[str, str],
    value_sets: dict[str, list[str]],
) -> dict[str, Any]:
    acc = _ProfileAccumulator()
    for el in sd.get("differential", {}).get("element", []):
        _record_differential_element(el, sd_type_by_url, value_sets, acc)

    for el in sd.get("snapshot", {}).get("element", []):
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
        "slices": [s for s in acc.slices.values() if s["min"] >= 1 and s["matchers"]],
    }


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
            "slices": [*(parent["slices"] if parent else []), *spec["slices"]],
        }
        resolved[url] = merged
        return merged

    for url in profiles:
        _resolve(url, set())
    return resolved


def _generate_all_ig_profiles(ig_pkgs: list[Path], value_sets: dict[str, list[str]]) -> str:
    """Extract constraint specs with baseDefinition inheritance across configured IG packages."""
    sd_type_by_url = _collect_sd_types(ig_pkgs)
    profiles: dict[str, dict[str, Any]] = {}
    for pkg in ig_pkgs:
        if not pkg.exists():
            continue
        for path in sorted(pkg.glob("StructureDefinition-*.json")):
            sd = json.loads(path.read_text(encoding="utf-8"))
            url = sd.get("url")
            if not url or sd.get("kind") != "resource" or sd.get("derivation") != "constraint":
                continue
            profiles[url] = _extract_profile_spec(sd, sd_type_by_url, value_sets)

    resolved = _resolve_all_profiles(profiles)
    header = (
        '"""Profile constraints extracted from R4 Core, '
        'CA-Baseline, CA-Core, IPS, and US Core IGs."""\n\n'
    )
    return (
        header
        + "from typing import Any\n\n"
        + f"PROFILE_CONSTRAINTS: dict[str, dict[str, Any]] = {resolved!r}\n"
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
    value_sets = _load_terminology(R4_PKG)
    sds = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(R4_PKG.glob("StructureDefinition-*.json"))
    ]
    complex_sds = [
        s
        for s in sds
        if s.get("kind") == "complex-type"
        and not s.get("abstract")
        and s.get("derivation") == "specialization"
    ]
    known_types = {s["id"] for s in complex_sds} | {"Element", "BackboneElement"}
    _write_complex_types(complex_sds, value_sets, known_types)

    resource_sds = [
        s
        for s in sds
        if s.get("kind") == "resource"
        and not s.get("abstract")
        and s.get("derivation") == "specialization"
    ]
    res_names = _write_resources(resource_sds, value_sets, known_types)
    (OUT_DIR / "profiles.py").write_text(
        _generate_all_ig_profiles(IG_PKGS, value_sets), encoding="utf-8"
    )
    print(f"Generated {len(complex_sds)} complex types and {len(res_names)} R4 resources.")


if __name__ == "__main__":
    main()
