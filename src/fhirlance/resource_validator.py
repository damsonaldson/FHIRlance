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
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.terminology import (
    TxOptions,
    parse_tx_options,
    validate_binding_value,
    validate_standalone_codings,
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


def _apply_binding_values(
    val: Any,
    full_path: str,
    b_info: dict[str, str],
    ctx: _BindingValidationCtx,
) -> None:
    vs_url = b_info["value_set"]
    res = validate_binding_value(
        val,
        full_path,
        vs_url,
        b_info["strength"],
        ctx.tx_options,
        vs_spec=VALUE_SET_SPECS.get(vs_url),
        complete_systems=COMPLETE_CODE_SYSTEMS,
    )
    ctx.issues.extend(res.errors)
    if ctx.warnings is not None and res.warnings:
        ctx.warnings.extend(res.warnings)


def _check_bindings_for_node(
    node: dict[str, Any],
    bindings: dict[str, dict[str, str]],
    prefix: str,
    ctx: _BindingValidationCtx,
) -> None:
    for rel_path, b_info in bindings.items():
        full_path = f"{prefix}.{rel_path}"
        if ctx.skip_paths and full_path in ctx.skip_paths:
            continue
        parts = tuple(p for p in rel_path.split(".") if p)
        for val in resolve_nodes(node, parts):
            _apply_binding_values(val, full_path, b_info, ctx)


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
    type_bindings = COMPLEX_TYPE_BINDINGS.get(model_cls.__name__)
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
    base_bindings = BASE_RESOURCE_BINDINGS.get(rtype)
    if not base_bindings:
        return
    _check_bindings_for_node(resource, base_bindings, rtype, ctx)


def _validate_standalone_and_base_bindings(
    resource: dict[str, Any],
    rtype: str,
    tx_options: TxOptions,
    issues: list[str],
    **kwargs: Any,
) -> None:
    standalone_res = validate_standalone_codings(
        resource, tx_options, complete_systems=COMPLETE_CODE_SYSTEMS
    )
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

    if tx_options.mode != "off":
        _validate_standalone_and_base_bindings(
            resource,
            rtype,
            tx_options,
            issues,
            warnings=_warnings_out,
            skip_paths=profile_bound_paths,
            model_cls=model_cls,
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
