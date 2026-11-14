"""FHIRPath invariant evaluators beyond JSON Schema and cardinality."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_OBS_VALUE_FIELDS = (
    "valueQuantity",
    "valueCodeableConcept",
    "valueString",
    "valueBoolean",
    "valueInteger",
    "valueRange",
    "valueRatio",
    "valueSampledData",
    "valueTime",
    "valueDateTime",
    "valuePeriod",
)
_COND_ABATEMENT_FIELDS = (
    "abatementDateTime",
    "abatementAge",
    "abatementPeriod",
    "abatementRange",
    "abatementString",
)
_PATIENT_CONTACT_FIELDS = ("name", "telecom", "address", "organization")
_BUNDLE_TOTAL_TYPES = frozenset({"searchset", "history"})
_BUNDLE_REQUEST_TYPES = frozenset({"batch", "transaction", "history"})
_BUNDLE_RESPONSE_TYPES = frozenset({"batch-response", "transaction-response", "history"})
_BUNDLE_UNIQUE_FULLURL_TYPES = frozenset({"document", "collection"})


def _coding_signatures(codeable_concept: Any) -> set[tuple[str | None, str | None]]:
    if not isinstance(codeable_concept, dict):
        return set()
    return {
        (coding.get("system"), coding.get("code"))
        for coding in (codeable_concept.get("coding") or [])
        if isinstance(coding, dict) and coding.get("code") is not None
    }


def _check_narrative_txt_1(resource: dict[str, Any]) -> list[str]:
    text_obj = resource.get("text")
    if not isinstance(text_obj, dict):
        return []
    div = text_obj.get("div")
    if isinstance(div, str) and "<div" not in div:
        return ["Invariant[txt-1]: Narrative.div SHALL be wrapped in a <div> element"]
    return []


def _check_patient_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for idx, contact in enumerate(resource.get("contact") or []):
        if isinstance(contact, dict) and not any(
            contact.get(field) for field in _PATIENT_CONTACT_FIELDS
        ):
            issues.append(
                f"Invariant[pat-1] contact[{idx}]: "
                "SHALL contain name, telecom, address, or organization"
            )
    return issues


def _check_observation_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    has_val = any(resource.get(field) is not None for field in _OBS_VALUE_FIELDS)
    if not has_val:
        return issues

    if resource.get("dataAbsentReason") is not None:
        issues.append(
            "Invariant[obs-6]: "
            "dataAbsentReason SHALL only be present if Observation.value[x] is absent"
        )

    components = resource.get("component")
    if not isinstance(components, list):
        return issues

    obs_codes = _coding_signatures(resource.get("code"))
    if not obs_codes:
        return issues

    for idx, comp in enumerate(components):
        comp_codes = _coding_signatures(comp.get("code") if isinstance(comp, dict) else None)
        if obs_codes & comp_codes:
            issues.append(
                f"Invariant[obs-7] component[{idx}]: "
                "component.code SHALL NOT match Observation.code when value[x] is present"
            )
    return issues


def _check_condition_invariants(resource: dict[str, Any]) -> list[str]:
    if resource.get("clinicalStatus") is None and any(
        resource.get(field) is not None for field in _COND_ABATEMENT_FIELDS
    ):
        return ["Invariant[con-4]: If condition is abated, clinicalStatus must be present"]
    return []


def _entry_version_id(entry: dict[str, Any]) -> str | None:
    res = entry.get("resource")
    if not isinstance(res, dict):
        return None
    meta = res.get("meta")
    if not isinstance(meta, dict):
        return None
    version = meta.get("versionId")
    return version if isinstance(version, str) else None


def _check_bundle_entry(
    entry: dict[str, Any],
    idx: int,
    bundle_type: Any,
    seen_keys: set[tuple[str, str | None]],
) -> list[str]:
    issues: list[str] = []
    if entry.get("request") is not None and bundle_type not in _BUNDLE_REQUEST_TYPES:
        issues.append(
            f"Invariant[bdl-3] entry[{idx}]: "
            "entry.request only allowed in batch/transaction/history"
        )
    if entry.get("response") is not None and bundle_type not in _BUNDLE_RESPONSE_TYPES:
        issues.append(
            f"Invariant[bdl-4] entry[{idx}]: "
            "entry.response only allowed in response/history bundles"
        )
    full_url = entry.get("fullUrl")
    if bundle_type in _BUNDLE_UNIQUE_FULLURL_TYPES and isinstance(full_url, str):
        key = (full_url, _entry_version_id(entry))
        if key in seen_keys:
            issues.append(f"Invariant[bdl-7] entry[{idx}]: duplicate fullUrl '{full_url}'")
        seen_keys.add(key)
    return issues


def _check_bundle_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    bundle_type = resource.get("type")
    if resource.get("total") is not None and bundle_type not in _BUNDLE_TOTAL_TYPES:
        issues.append(
            f"Invariant[bdl-1]: Bundle.total only allowed on searchset/history, not '{bundle_type}'"
        )

    seen_keys: set[tuple[str, str | None]] = set()
    for idx, entry in enumerate(resource.get("entry") or []):
        if isinstance(entry, dict):
            issues.extend(_check_bundle_entry(entry, idx, bundle_type, seen_keys))
    return issues


_RESOURCE_INVARIANT_CHECKS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "Patient": _check_patient_invariants,
    "Observation": _check_observation_invariants,
    "Condition": _check_condition_invariants,
    "Bundle": _check_bundle_invariants,
}


def check_fhirpath_invariants(resource: dict[str, Any], rtype: str) -> list[str]:
    """Evaluate core FHIRPath invariants beyond structural schema and cardinality."""
    issues = _check_narrative_txt_1(resource)
    checker = _RESOURCE_INVARIANT_CHECKS.get(rtype)
    if checker is not None:
        issues.extend(checker(resource))
    return issues
