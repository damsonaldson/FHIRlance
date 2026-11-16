"""Core single-resource FHIR R4 structural, invariant, and IG profile validator."""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from fhirlance.base import FHIRBaseModel
from fhirlance.extensions import COMPILED_EXTENSIONS, CompiledExtension, validate_extensions
from fhirlance.ig_loader import load_compiled_ig_bundle
from fhirlance.invariants import check_fhirpath_invariants
from fhirlance.primitive_extensions import (
    has_primitive_extension_error,
    strip_and_validate_primitive_extensions,
)
from fhirlance.profile_engine import (
    COMPILED_PROFILES,
    extract_relative_ref,
    resolve_nodes,
    validate_single_profile,
)
from fhirlance.profiles import (
    BASE_RESOURCE_BINDINGS,
    COMPLETE_CODE_SYSTEMS,
    COMPLEX_TYPE_BINDINGS,
    VALUE_SET_SPECS,
)
from fhirlance.questionnaire import (
    validate_questionnaire_response_against_questionnaire,
    validate_questionnaire_semantics,
)
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.terminology import (
    TerminologyResult,
    TxOptions,
    parse_tx_options,
    scan_and_validate_standalone_codings,
    validate_binding_value,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from pathlib import Path

    from fhirlance.profile_engine import CompiledProfile

_MAX_RECURSION_DEPTH = 16


def _format_validation_errors(exc: ValidationError) -> list[str]:
    return [
        f"Structural[{'.'.join(str(part) for part in err['loc'])}]: {err['msg']}"
        for err in exc.errors()
    ]


def _validate_structure(resource: dict[str, Any], model_cls: type[FHIRBaseModel]) -> list[str]:
    try:
        model_cls.model_validate(resource)
    except ValidationError as exc:
        if not has_primitive_extension_error(exc):
            return _format_validation_errors(exc)

        issues: list[str] = []
        sanitized = strip_and_validate_primitive_extensions(resource, model_cls, issues)
        try:
            model_cls.model_validate(sanitized, context={"prim_exts_validated": True})
        except ValidationError as exc2:
            issues.extend(_format_validation_errors(exc2))
        return issues
    return []


def _extract_declared_profiles(resource: dict[str, Any]) -> list[str]:
    meta = resource.get("meta")
    if not isinstance(meta, dict):
        return []
    raw_profiles = meta.get("profile")
    if not isinstance(raw_profiles, list):
        return []
    return [p for p in raw_profiles if isinstance(p, str)]


def _collect_profile_binding_paths(
    effective_profiles: list[str],
    profiles_dict: dict[str, CompiledProfile],
) -> set[str]:
    bound: set[str] = set()
    for prof_url in effective_profiles:
        prof = profiles_dict.get(prof_url)
        if prof is not None:
            for rule in prof.binding_specs:
                bound.add(rule.path)
    return bound


@dataclass(frozen=True, slots=True)
class _ComplexFieldStep:
    json_key: str
    child_model: type[FHIRBaseModel]


@dataclass(frozen=True, slots=True)
class _BindingValidationCtx:
    tx_options: TxOptions
    issues: list[str]
    warnings: list[str] | None
    skip_paths: set[str] | None


def _unwrap_model_type(annotation: Any) -> type[FHIRBaseModel] | None:
    if isinstance(annotation, type) and issubclass(annotation, FHIRBaseModel):
        return annotation
    for arg in getattr(annotation, "__args__", ()):
        found = _unwrap_model_type(arg)
        if found is not None:
            return found
    return None


@cache
def _can_reach_complex_binding(model_cls: type[FHIRBaseModel]) -> bool:
    stack: list[type[FHIRBaseModel]] = [model_cls]
    seen: set[type[FHIRBaseModel]] = set()
    while stack:
        curr = stack.pop()
        if curr in seen:
            continue
        seen.add(curr)
        if curr.__name__ in COMPLEX_TYPE_BINDINGS:
            return True
        for field_name, field_info in curr.model_fields.items():
            if field_name in ("extension", "modifierExtension"):
                continue
            child = _unwrap_model_type(field_info.annotation)
            if child is not None and child not in seen:
                stack.append(child)
    return False


@cache
def _complex_binding_plan(model_cls: type[FHIRBaseModel]) -> tuple[_ComplexFieldStep, ...]:
    steps: list[_ComplexFieldStep] = []
    for field_name, field_info in model_cls.model_fields.items():
        if field_name in ("extension", "modifierExtension"):
            continue
        child_model = _unwrap_model_type(field_info.annotation)
        if child_model is None or not _can_reach_complex_binding(child_model):
            continue
        steps.append(
            _ComplexFieldStep(
                json_key=field_info.alias or field_name,
                child_model=child_model,
            )
        )
    return tuple(steps)


@dataclass(frozen=True, slots=True)
class _CompiledBindingEntry:
    rel_path: str
    first_key: str
    parts: tuple[str, ...]
    value_set: str
    strength: str


def _compile_binding_map(
    raw_bindings: dict[str, dict[str, str]] | None,
) -> tuple[_CompiledBindingEntry, ...]:
    if not raw_bindings:
        return ()
    entries: list[_CompiledBindingEntry] = []
    for rel_path, b_info in raw_bindings.items():
        parts = tuple(p for p in rel_path.split(".") if p)
        first_key = "" if not parts or parts[0].endswith("[x]") else parts[0]
        entries.append(
            _CompiledBindingEntry(
                rel_path=rel_path,
                first_key=first_key,
                parts=parts,
                value_set=b_info["value_set"],
                strength=b_info["strength"],
            )
        )
    return tuple(entries)


@cache
def _compiled_base_bindings(rtype: str) -> tuple[_CompiledBindingEntry, ...]:
    return _compile_binding_map(BASE_RESOURCE_BINDINGS.get(rtype))


@cache
def _compiled_complex_bindings(type_name: str) -> tuple[_CompiledBindingEntry, ...]:
    return _compile_binding_map(COMPLEX_TYPE_BINDINGS.get(type_name))


def _apply_binding_values(
    val: Any,
    full_path: str,
    entry: _CompiledBindingEntry,
    ctx: _BindingValidationCtx,
) -> None:
    res = validate_binding_value(
        val,
        full_path,
        entry.value_set,
        entry.strength,
        ctx.tx_options,
        vs_spec=VALUE_SET_SPECS.get(entry.value_set),
        complete_systems=COMPLETE_CODE_SYSTEMS,
    )
    ctx.issues.extend(res.errors)
    if ctx.warnings is not None and res.warnings:
        ctx.warnings.extend(res.warnings)


def _apply_direct_binding(
    val: Any,
    full_path: str,
    entry: _CompiledBindingEntry,
    ctx: _BindingValidationCtx,
) -> None:
    if val is None:
        return
    if isinstance(val, list):
        for item in val:
            if item is not None:
                _apply_binding_values(item, full_path, entry, ctx)
        return
    _apply_binding_values(val, full_path, entry, ctx)


def _check_bindings_for_node(
    node: dict[str, Any],
    bindings: tuple[_CompiledBindingEntry, ...],
    prefix: str,
    ctx: _BindingValidationCtx,
) -> None:
    for entry in bindings:
        if entry.first_key and entry.first_key not in node:
            continue
        full_path = f"{prefix}.{entry.rel_path}"
        if ctx.skip_paths and full_path in ctx.skip_paths:
            continue
        if len(entry.parts) == 1 and entry.first_key:
            _apply_direct_binding(node[entry.first_key], full_path, entry, ctx)
        else:
            for val in resolve_nodes(node, entry.parts):
                _apply_binding_values(val, full_path, entry, ctx)


def _iter_child_dicts(child: Any) -> Iterator[dict[str, Any]]:
    if isinstance(child, dict):
        if not isinstance(child.get("resourceType"), str):
            yield child
        return
    if isinstance(child, list):
        for item in child:
            if isinstance(item, dict) and not isinstance(item.get("resourceType"), str):
                yield item


def _walk_complex_bindings(
    node: dict[str, Any],
    model_cls: type[FHIRBaseModel],
    current_path: str,
    ctx: _BindingValidationCtx,
) -> None:
    type_bindings = _compiled_complex_bindings(model_cls.__name__)
    if type_bindings:
        _check_bindings_for_node(node, type_bindings, current_path, ctx)
    for step in _complex_binding_plan(model_cls):
        child = node.get(step.json_key)
        if child is None:
            continue
        child_path = f"{current_path}.{step.json_key}"
        for sub in _iter_child_dicts(child):
            _walk_complex_bindings(sub, step.child_model, child_path, ctx)


def _validate_base_bindings(
    resource: dict[str, Any],
    rtype: str,
    ctx: _BindingValidationCtx,
) -> None:
    base_bindings = _compiled_base_bindings(rtype)
    if not base_bindings:
        return
    _check_bindings_for_node(resource, base_bindings, rtype, ctx)


def _validate_bindings_and_append_standalone(
    resource: dict[str, Any],
    rtype: str,
    tx_options: TxOptions,
    issues: list[str],
    **kwargs: Any,
) -> None:
    standalone_res: TerminologyResult = kwargs["standalone_res"]
    issues.extend(standalone_res.errors)
    warnings: list[str] | None = kwargs.get("warnings")
    if warnings is not None and standalone_res.warnings:
        warnings.extend(standalone_res.warnings)
    ctx = _BindingValidationCtx(
        tx_options=tx_options,
        issues=issues,
        warnings=warnings,
        skip_paths=kwargs.get("skip_paths"),
    )
    _validate_base_bindings(resource, rtype, ctx)
    model_cls: type[FHIRBaseModel] | None = kwargs.get("model_cls") or RESOURCE_MODELS.get(rtype)
    if model_cls is not None:
        _walk_complex_bindings(resource, model_cls, rtype, ctx)


def _build_bundle_index(resource: dict[str, Any]) -> dict[str, dict[str, Any]] | None:
    entries = resource.get("entry")
    if not isinstance(entries, list):
        return None
    index: dict[str, dict[str, Any]] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        entry_res = entry.get("resource")
        if not isinstance(entry_res, dict):
            continue
        full_url = entry.get("fullUrl")
        if isinstance(full_url, str) and full_url:
            index[full_url] = entry_res
            rel_ref = extract_relative_ref(full_url)
            if rel_ref is not None:
                index.setdefault(rel_ref, entry_res)
        e_rtype = entry_res.get("resourceType")
        e_rid = entry_res.get("id")
        if isinstance(e_rtype, str) and e_rtype and isinstance(e_rid, str) and e_rid:
            index[f"{e_rtype}/{e_rid}"] = entry_res
    return index or None


def _validate_nested_resources(
    resource: dict[str, Any],
    rtype: str,
    *,
    ig_sources: Sequence[str | Path] | dict[str, CompiledProfile] | None,
    **kwargs: Any,
) -> list[str]:
    depth: int = int(kwargs.get("depth", 0))
    tx_options = kwargs.get("tx")
    warnings_out: list[str] | None = kwargs.get("_warnings_out")
    compiled_extensions = kwargs.get("_compiled_extensions")
    bundle_index: dict[str, dict[str, Any]] | None = kwargs.get("_bundle_index")
    skip_nested_entries = bool(kwargs.get("_skip_nested_entries", False))
    issues: list[str] = []
    contained = resource.get("contained")
    if isinstance(contained, list):
        for idx, sub in enumerate(contained):
            sub_warnings: list[str] | None = [] if warnings_out is not None else None
            sub_issues = validate_resource(
                sub,
                ig_sources=ig_sources,
                _depth=depth + 1,
                tx=tx_options,
                _warnings_out=sub_warnings,
                _compiled_extensions=compiled_extensions,
                _bundle_index=bundle_index,
            )
            issues.extend(f"contained[{idx}]: {msg}" for msg in sub_issues)
            if warnings_out is not None and sub_warnings:
                warnings_out.extend(f"contained[{idx}]: {msg}" for msg in sub_warnings)

    if not skip_nested_entries and rtype == "Bundle" and isinstance(resource.get("entry"), list):
        for idx, entry in enumerate(resource["entry"]):
            if isinstance(entry, dict) and entry.get("resource") is not None:
                sub_warnings = [] if warnings_out is not None else None
                sub_issues = validate_resource(
                    entry["resource"],
                    ig_sources=ig_sources,
                    _depth=depth + 1,
                    tx=tx_options,
                    _warnings_out=sub_warnings,
                    _compiled_extensions=compiled_extensions,
                    _bundle_index=bundle_index,
                )
                issues.extend(f"entry[{idx}].resource: {msg}" for msg in sub_issues)
                if warnings_out is not None and sub_warnings:
                    warnings_out.extend(f"entry[{idx}].resource: {msg}" for msg in sub_warnings)
    return issues


def _resolve_compiled_maps(
    ig_sources: Sequence[str | Path] | dict[str, CompiledProfile] | None,
    ext_override: dict[str, CompiledExtension] | None,
) -> tuple[dict[str, CompiledProfile] | None, dict[str, CompiledExtension]]:
    if isinstance(ig_sources, dict):
        return ig_sources, ext_override if ext_override is not None else COMPILED_EXTENSIONS
    if ig_sources:
        prof_map, ext_map = load_compiled_ig_bundle(ig_sources)
        return prof_map, ext_override if ext_override is not None else ext_map
    return None, ext_override if ext_override is not None else COMPILED_EXTENSIONS


def _resolve_questionnaire(
    canonical: str,
    bundle_index: dict[str, dict[str, Any]] | None,
    contained: Any,
) -> dict[str, Any] | None:
    if canonical.startswith("#"):
        target_id = canonical[1:]
        if isinstance(contained, list):
            for item in contained:
                if (
                    isinstance(item, dict)
                    and item.get("resourceType") == "Questionnaire"
                    and item.get("id") == target_id
                ):
                    return item
        return None

    if bundle_index is None:
        return None

    canonical_no_ver = canonical.split("|", 1)[0]
    direct = bundle_index.get(canonical) or bundle_index.get(canonical_no_ver)
    if isinstance(direct, dict) and direct.get("resourceType") == "Questionnaire":
        return direct

    for res in bundle_index.values():
        if res.get("resourceType") == "Questionnaire" and res.get("url") == canonical_no_ver:
            return res
    return None


def _validate_specialized_semantics(
    resource: dict[str, Any],
    rtype: str,
    tx_options: TxOptions,
    bundle_index: dict[str, dict[str, Any]] | None,
    kwargs: dict[str, Any],
) -> list[str]:
    if rtype == "Questionnaire":
        return validate_questionnaire_semantics(
            resource,
            tx_options=tx_options,
            warnings_out=kwargs.get("_warnings_out"),
        )
    if rtype == "QuestionnaireResponse":
        q_override = kwargs.get("questionnaire_resource")
        q_res = q_override if isinstance(q_override, dict) else None
        if q_res is None and isinstance(q_ref := resource.get("questionnaire"), str) and q_ref:
            q_res = _resolve_questionnaire(q_ref, bundle_index, resource.get("contained"))
        if q_res is not None:
            return validate_questionnaire_response_against_questionnaire(
                resource, q_res, tx_options=tx_options
            )
    return []


def validate_resource(
    resource: Any,
    *,
    profile_urls: list[str] | tuple[str, ...] | None = None,
    ig_sources: Sequence[str | Path] | dict[str, CompiledProfile] | None = None,
    **kwargs: Any,
) -> list[str]:
    """Validate any FHIR R4 resource structurally, recursively, and against IG profiles."""
    depth: int = int(kwargs.get("_depth", 0))
    if depth > _MAX_RECURSION_DEPTH:
        return [f"Maximum resource nesting depth ({_MAX_RECURSION_DEPTH}) exceeded"]
    if type(resource) is not dict:
        return [f"Resource must be a JSON object, got {type(resource).__name__}"]

    rtype = resource.get("resourceType")
    if not rtype or type(rtype) is not str:
        return ["Missing required field: 'resourceType'"]

    model_cls = RESOURCE_MODELS.get(rtype)
    if model_cls is None:
        return [f"Unknown FHIR R4 resourceType: '{rtype}'"]

    tx_raw = kwargs.get("tx", "local")
    strict_extensible = bool(kwargs.get("strict_extensible", False))
    _warnings_out: list[str] | None = kwargs.get("_warnings_out")
    tx_options = (
        tx_raw
        if isinstance(tx_raw, TxOptions)
        else parse_tx_options(tx_raw, strict_extensible=strict_extensible)
    )

    issues = _validate_structure(resource, model_cls)
    issues.extend(check_fhirpath_invariants(resource, rtype))

    declared_profiles = _extract_declared_profiles(resource)

    compiled_map, ext_dict = _resolve_compiled_maps(ig_sources, kwargs.get("_compiled_extensions"))
    profiles_dict = compiled_map if compiled_map is not None else COMPILED_PROFILES
    effective_profiles = list(dict.fromkeys([*declared_profiles, *(profile_urls or ())]))
    profile_bound_paths = _collect_profile_binding_paths(effective_profiles, profiles_dict)

    if tx_options.mode != "off":
        standalone_res, has_extensions = scan_and_validate_standalone_codings(
            resource, tx_options, complete_systems=COMPLETE_CODE_SYSTEMS
        )
        if has_extensions:
            issues.extend(
                validate_extensions(
                    resource,
                    model_cls,
                    rtype,
                    compiled_extensions=ext_dict,
                    tx=tx_options,
                    _warnings_out=_warnings_out,
                    _skip_precheck=True,
                )
            )
        _validate_bindings_and_append_standalone(
            resource,
            rtype,
            tx_options,
            issues,
            standalone_res=standalone_res,
            warnings=_warnings_out,
            skip_paths=profile_bound_paths,
            model_cls=model_cls,
        )
    else:
        issues.extend(
            validate_extensions(
                resource,
                model_cls,
                rtype,
                compiled_extensions=ext_dict,
                tx=tx_options,
                _warnings_out=_warnings_out,
            )
        )

    bundle_index: dict[str, dict[str, Any]] | None = kwargs.get("_bundle_index") or kwargs.get(
        "bundle_index"
    )
    if rtype == "Bundle":
        inner_index = _build_bundle_index(resource)
        if inner_index is not None:
            bundle_index = (
                {**bundle_index, **inner_index} if bundle_index is not None else inner_index
            )

    for prof_url in effective_profiles:
        issues.extend(
            validate_single_profile(
                resource,
                rtype,
                prof_url,
                compiled_profiles=profiles_dict,
                compiled_map=compiled_map,
                tx=tx_options,
                _warnings_out=_warnings_out,
                bundle_index=bundle_index,
            )
        )

    issues.extend(
        _validate_specialized_semantics(resource, rtype, tx_options, bundle_index, kwargs)
    )

    issues.extend(
        _validate_nested_resources(
            resource,
            rtype,
            ig_sources=compiled_map,
            depth=depth,
            tx=tx_options,
            _warnings_out=_warnings_out,
            _compiled_extensions=ext_dict,
            _bundle_index=bundle_index,
            _skip_nested_entries=bool(kwargs.get("_skip_nested_entries", False)),
        )
    )
    return issues
