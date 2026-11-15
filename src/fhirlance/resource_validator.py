"""Core single-resource FHIR R4 structural, invariant, and IG profile validator."""

from __future__ import annotations

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
from fhirlance.profile_engine import COMPILED_PROFILES, resolve_nodes, validate_single_profile
from fhirlance.profiles import (
    BASE_RESOURCE_BINDINGS,
    COMPLETE_CODE_SYSTEMS,
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
    from collections.abc import Sequence
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


def _validate_base_bindings(
    resource: dict[str, Any],
    rtype: str,
    tx_options: TxOptions,
    issues: list[str],
    **kwargs: Any,
) -> None:
    base_bindings = BASE_RESOURCE_BINDINGS.get(rtype)
    if not base_bindings:
        return
    warnings: list[str] | None = kwargs.get("warnings")
    skip_paths: set[str] | None = kwargs.get("skip_paths")
    for rel_path, b_info in base_bindings.items():
        full_path = f"{rtype}.{rel_path}"
        if skip_paths and full_path in skip_paths:
            continue
        parts = tuple(p for p in rel_path.split(".") if p)
        for val in resolve_nodes(resource, parts):
            vs_url = b_info["value_set"]
            res = validate_binding_value(
                val,
                full_path,
                vs_url,
                b_info["strength"],
                tx_options,
                vs_spec=VALUE_SET_SPECS.get(vs_url),
                complete_systems=COMPLETE_CODE_SYSTEMS,
            )
            issues.extend(res.errors)
            if warnings is not None and res.warnings:
                warnings.extend(res.warnings)


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
    _validate_base_bindings(resource, rtype, tx_options, issues, **kwargs)


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
            )
            issues.extend(f"contained[{idx}]: {msg}" for msg in sub_issues)
            if warnings_out is not None and sub_warnings:
                warnings_out.extend(f"contained[{idx}]: {msg}" for msg in sub_warnings)

    if rtype == "Bundle" and isinstance(resource.get("entry"), list):
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
        )

    for prof_url in effective_profiles:
        issues.extend(
            validate_single_profile(
                resource,
                rtype,
                prof_url,
                compiled_profiles=profiles_dict,
                tx=tx_options,
                _warnings_out=_warnings_out,
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
        )
    )
    return issues
