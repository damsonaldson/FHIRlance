"""Pan-Canadian FHIR R4 profile constants and localization checks."""

from __future__ import annotations

import re
from typing import Any

CA_BASELINE_PROFILES: dict[str, str] = {
    "Patient": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient",
    "Encounter": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-encounter",
    "Observation": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-observation",
    "Observation-Result": (
        "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-observation-results"
    ),
    "Observation-Vitals": (
        "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-observation-vital-signs"
    ),
    "Condition": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-condition",
    "Procedure": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-procedure",
    "MedicationRequest": (
        "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-medicationrequest"
    ),
    "DiagnosticReport": (
        "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-diagnosticreport"
    ),
    "Organization": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-organization",
    "Practitioner": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-practitioner",
}

PS_CA_PROFILES: dict[str, str] = {
    "Patient": "http://fhir.infoway-inforoute.ca/io/ps-ca/StructureDefinition/Patient-ca-ps",
    "Condition": "http://fhir.infoway-inforoute.ca/io/ps-ca/StructureDefinition/Condition-ca-ps",
    "MedicationRequest": (
        "http://fhir.infoway-inforoute.ca/io/ps-ca/StructureDefinition/MedicationRequest-ca-ps"
    ),
    "Observation": (
        "http://fhir.infoway-inforoute.ca/io/ps-ca/StructureDefinition/Observation-ca-ps"
    ),
}

PROVINCIAL_JHN_SYSTEMS: dict[str, str] = {
    "NS": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-ns-patient-health-card-number",
    "ON": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-on-patient-health-card-number",
    "BC": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-bc-patient-health-card-number",
    "AB": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-ab-patient-health-card-number",
    "QC": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-qc-patient-health-card-number",
    "MB": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-mb-patient-health-card-number",
    "SK": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-sk-patient-health-card-number",
    "NB": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-nb-patient-health-card-number",
    "NL": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-nl-patient-health-card-number",
    "PE": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-pe-patient-health-card-number",
    "YT": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-yt-patient-health-card-number",
    "NT": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-nt-patient-health-card-number",
    "NU": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-nu-patient-health-card-number",
}

CANADIAN_POSTAL_REGEX = re.compile(
    r"^[A-CEGHJ-NPR-TVXY]\d[A-CEGHJ-NPR-TV-Z] \d[A-CEGHJ-NPR-TV-Z]\d$"
)
CANADIAN_PROVINCES = frozenset(PROVINCIAL_JHN_SYSTEMS.keys())
CA_BASE_PROFILE_VALUES = frozenset(CA_BASELINE_PROFILES.values())
PS_CA_PROFILE_VALUES = frozenset(PS_CA_PROFILES.values())
DEFINED_PROFILE_TYPES = frozenset(CA_BASELINE_PROFILES) | frozenset(PS_CA_PROFILES)
PROVINCIAL_JHN_VALUES = tuple(PROVINCIAL_JHN_SYSTEMS.values())

_ALLOWED_COUNTRIES = frozenset({"CA", "CAN", "Canada"})
_DISALLOWED_US_EXTENSION_MARKERS = ("us-core-race", "us-core-ethnicity")


def _is_jhn_identifier(identifier: Any) -> bool:
    if not isinstance(identifier, dict):
        return False

    ident_type = identifier.get("type")
    codings = ident_type.get("coding") if isinstance(ident_type, dict) else None
    if isinstance(codings, list) and any(
        isinstance(c, dict) and c.get("code") == "JHN" for c in codings
    ):
        return True

    system = identifier.get("system")
    return isinstance(system, str) and any(sys_uri in system for sys_uri in PROVINCIAL_JHN_VALUES)


def _validate_canadian_addresses(addresses: Any) -> list[str]:
    if not isinstance(addresses, list):
        return []

    issues: list[str] = []
    for idx, addr in enumerate(addresses):
        if not isinstance(addr, dict):
            continue
        country = addr.get("country", "")
        if country not in _ALLOWED_COUNTRIES:
            issues.append(f"Address[{idx}] country is '{country}', expected 'CA'")
        prov = addr.get("state", "")
        if prov not in CANADIAN_PROVINCES:
            issues.append(f"Address[{idx}] state is '{prov}', expected Canadian province code")
        pcode = addr.get("postalCode", "")
        if pcode and not CANADIAN_POSTAL_REGEX.match(str(pcode)):
            issues.append(
                f"Address[{idx}] postalCode '{pcode}' does not match Canadian format 'A1A 1A1'"
            )
    return issues


def _check_disallowed_us_extensions(extensions: Any) -> list[str]:
    if not isinstance(extensions, list):
        return []

    issues: list[str] = []
    for ext in extensions:
        if not isinstance(ext, dict):
            continue
        url = str(ext.get("url", ""))
        if any(marker in url for marker in _DISALLOWED_US_EXTENSION_MARKERS):
            issues.append(f"Patient contains US-only extension: '{url}'")
    return issues


def validate_canadian_patient(resource: dict[str, Any]) -> list[str]:
    """Validate Patient-specific Canadian JHN, address, and US-extension rules."""
    issues: list[str] = []
    identifiers = resource.get("identifier")
    ident_list = identifiers if isinstance(identifiers, list) else []
    if not any(_is_jhn_identifier(ident) for ident in ident_list):
        issues.append("Patient missing Canadian Jurisdictional Health Number (JHN) identifier")

    issues.extend(_validate_canadian_addresses(resource.get("address")))
    issues.extend(_check_disallowed_us_extensions(resource.get("extension")))
    return issues


def validate_canadian_rules(
    resource: dict[str, Any],
    rtype: str,
    declared_profiles: list[str],
) -> list[str]:
    """Enforce Canadian meta.profile presence and Patient JHN/address/extension rules."""
    issues: list[str] = []
    if rtype in DEFINED_PROFILE_TYPES or rtype.startswith("Observation"):
        has_ca = any(
            p in CA_BASE_PROFILE_VALUES
            or p in PS_CA_PROFILE_VALUES
            or "ca/baseline" in p
            or "ps-ca" in p
            for p in declared_profiles
        )
        if not has_ca:
            issues.append(
                f"Resource {rtype}/{resource.get('id')} has no Canadian meta.profile attached"
            )
    if rtype == "Patient":
        issues.extend(validate_canadian_patient(resource))
    return issues
