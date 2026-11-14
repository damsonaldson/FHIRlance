"""Core single-resource FHIR R4 structural, invariant, and IG profile validator."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from fhirlance.base import FHIRBaseModel
from fhirlance.canadian import validate_canadian_rules
from fhirlance.ig_loader import load_compiled_ig_profiles
from fhirlance.invariants import check_fhirpath_invariants
from fhirlance.primitive_extensions import (
    has_primitive_extension_error,
    strip_and_validate_primitive_extensions,
)
from fhirlance.profile_engine import COMPILED_PROFILES, validate_single_profile
from fhirlance.resources import RESOURCE_MODELS

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


def _validate_nested_resources(
    resource: dict[str, Any],
    rtype: str,
    *,
    require_canadian_profile: bool,
    ig_sources: Sequence[str | Path] | dict[str, CompiledProfile] | None,
    depth: int,
) -> list[str]:
    issues: list[str] = []
    contained = resource.get("contained")
    if isinstance(contained, list):
        for idx, sub in enumerate(contained):
            sub_issues = validate_resource(
                sub,
                require_canadian_profile=False,
                ig_sources=ig_sources,
                _depth=depth + 1,
            )
            issues.extend(f"contained[{idx}]: {msg}" for msg in sub_issues)

    if rtype == "Bundle" and isinstance(resource.get("entry"), list):
        for idx, entry in enumerate(resource["entry"]):
            if isinstance(entry, dict) and entry.get("resource") is not None:
                sub_issues = validate_resource(
                    entry["resource"],
                    require_canadian_profile=require_canadian_profile,
                    ig_sources=ig_sources,
                    _depth=depth + 1,
                )
                issues.extend(f"entry[{idx}].resource: {msg}" for msg in sub_issues)
    return issues


def _resolve_compiled_map(
    ig_sources: Sequence[str | Path] | dict[str, CompiledProfile] | None,
) -> dict[str, CompiledProfile] | None:
    if isinstance(ig_sources, dict):
        return ig_sources
    if ig_sources:
        return load_compiled_ig_profiles(ig_sources)
    return None


def validate_resource(
    resource: Any,
    *,
    require_canadian_profile: bool = True,
    profile_urls: list[str] | None = None,
    ig_sources: Sequence[str | Path] | dict[str, CompiledProfile] | None = None,
    _depth: int = 0,
) -> list[str]:
    """Validate any FHIR R4 resource structurally, recursively, and against IG profiles."""
    if _depth > _MAX_RECURSION_DEPTH:
        return [f"Maximum resource nesting depth ({_MAX_RECURSION_DEPTH}) exceeded"]
    if type(resource) is not dict:
        return [f"Resource must be a JSON object, got {type(resource).__name__}"]

    rtype = resource.get("resourceType")
    if not rtype or type(rtype) is not str:
        return ["Missing required field: 'resourceType'"]

    model_cls = RESOURCE_MODELS.get(rtype)
    if model_cls is None:
        return [f"Unknown FHIR R4 resourceType: '{rtype}'"]

    issues = _validate_structure(resource, model_cls)
    issues.extend(check_fhirpath_invariants(resource, rtype))

    declared_profiles = _extract_declared_profiles(resource)
    if require_canadian_profile:
        issues.extend(validate_canadian_rules(resource, rtype, declared_profiles))

    compiled_map = _resolve_compiled_map(ig_sources)
    profiles_dict = compiled_map if compiled_map is not None else COMPILED_PROFILES
    effective_profiles = list(dict.fromkeys([*declared_profiles, *(profile_urls or ())]))
    for prof_url in effective_profiles:
        issues.extend(
            validate_single_profile(resource, rtype, prof_url, compiled_profiles=profiles_dict)
        )

    issues.extend(
        _validate_nested_resources(
            resource,
            rtype,
            require_canadian_profile=require_canadian_profile,
            ig_sources=compiled_map,
            depth=_depth,
        )
    )
    return issues
