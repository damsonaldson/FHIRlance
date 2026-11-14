"""Output formatters for FHIRlance reports: OperationOutcome, SARIF, JUnit, JSON, and Text."""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fhirlance.resource_validator import validate_resource

if TYPE_CHECKING:
    from collections.abc import Sequence

SUPPORTED_OUTPUT_FORMATS: tuple[str, ...] = (
    "text",
    "json",
    "operation-outcome",
    "sarif",
    "junit",
)

FHIR_RESOURCE_TYPES: frozenset[str] = frozenset(
    (
        "Account",
        "ActivityDefinition",
        "AdverseEvent",
        "AllergyIntolerance",
        "Appointment",
        "AppointmentResponse",
        "AuditEvent",
        "Basic",
        "Binary",
        "BiologicallyDerivedProduct",
        "BodyStructure",
        "Bundle",
        "CapabilityStatement",
        "CarePlan",
        "CareTeam",
        "CatalogEntry",
        "ChargeItem",
        "ChargeItemDefinition",
        "Claim",
        "ClaimResponse",
        "ClinicalImpression",
        "CodeSystem",
        "Communication",
        "CommunicationRequest",
        "CompartmentDefinition",
        "Composition",
        "ConceptMap",
        "Condition",
        "Consent",
        "Contract",
        "Coverage",
        "CoverageEligibilityRequest",
        "CoverageEligibilityResponse",
        "DetectedIssue",
        "Device",
        "DeviceDefinition",
        "DeviceMetric",
        "DeviceRequest",
        "DeviceUseStatement",
        "DiagnosticReport",
        "DocumentManifest",
        "DocumentReference",
        "EffectEvidenceSynthesis",
        "Encounter",
        "Endpoint",
        "EnrollmentRequest",
        "EnrollmentResponse",
        "EpisodeOfCare",
        "EventDefinition",
        "Evidence",
        "EvidenceVariable",
        "ExampleScenario",
        "ExplanationOfBenefit",
        "FamilyMemberHistory",
        "Flag",
        "Goal",
        "GraphDefinition",
        "Group",
        "GuidanceResponse",
        "HealthcareService",
        "ImagingStudy",
        "Immunization",
        "ImmunizationEvaluation",
        "ImmunizationRecommendation",
        "ImplementationGuide",
        "InsurancePlan",
        "Invoice",
        "Library",
        "Linkage",
        "List",
        "Location",
        "Measure",
        "MeasureReport",
        "Media",
        "Medication",
        "MedicationAdministration",
        "MedicationDispense",
        "MedicationKnowledge",
        "MedicationRequest",
        "MedicationStatement",
        "MedicinalProduct",
        "MedicinalProductAuthorization",
        "MedicinalProductContraindication",
        "MedicinalProductIndication",
        "MedicinalProductIngredient",
        "MedicinalProductInteraction",
        "MedicinalProductManufactured",
        "MedicinalProductPackaged",
        "MedicinalProductPharmaceutical",
        "MedicinalProductUndesirableEffect",
        "MessageDefinition",
        "MessageHeader",
        "MolecularSequence",
        "NamingSystem",
        "NutritionOrder",
        "Observation",
        "ObservationDefinition",
        "OperationDefinition",
        "OperationOutcome",
        "Organization",
        "OrganizationAffiliation",
        "Parameters",
        "Patient",
        "PaymentNotice",
        "PaymentReconciliation",
        "Person",
        "PlanDefinition",
        "Practitioner",
        "PractitionerRole",
        "Procedure",
        "Provenance",
        "Questionnaire",
        "QuestionnaireResponse",
        "RelatedPerson",
        "RequestGroup",
        "ResearchDefinition",
        "ResearchElementDefinition",
        "ResearchStudy",
        "ResearchSubject",
        "RiskAssessment",
        "RiskEvidenceSynthesis",
        "Schedule",
        "SearchParameter",
        "ServiceRequest",
        "Slot",
        "Specimen",
        "SpecimenDefinition",
        "StructureDefinition",
        "StructureMap",
        "Subscription",
        "Substance",
        "SubstanceNucleicAcid",
        "SubstancePolymer",
        "SubstanceProtein",
        "SubstanceReferenceInformation",
        "SubstanceSourceMaterial",
        "SubstanceSpecification",
        "SupplyDelivery",
        "SupplyRequest",
        "Task",
        "TerminologyCapabilities",
        "TestReport",
        "TestScript",
        "ValueSet",
        "VerificationResult",
        "VisionPrescription",
    )
)

_STRUCTURE_STARTS: tuple[str, ...] = (
    "Structural[",
    "Resource must be",
    "Missing required field",
    "Unknown FHIR R4 resourceType",
    "Maximum resource nesting",
)

_RE_NESTED_PREFIXES = re.compile(r"entry\[\d+\]\.resource|contained\[\d+\]")
_RE_NESTED_STRIP = re.compile(r"^(?:(?:entry\[\d+\]\.resource|contained\[\d+\]):\s*)+")
_RE_STRUCTURAL_LOC = re.compile(r"Structural\[(.*?)\]")
_RE_PROFILE_PATH = re.compile(r"Profile\[.*?\]:.*?['\"]([A-Za-z][A-Za-z0-9_.[\]]+)['\"]")
_RE_INVARIANT_PATH = re.compile(r"Invariant\[.*?\]\s+([A-Za-z0-9_.[\]]+):")
_RE_BARE_PATH = re.compile(r"^['\"]([A-Za-z][A-Za-z0-9_.[\]]+)['\"](?:\s*code|:)")
_RE_ADDRESS_PATH = re.compile(r"(Address\[\d+\])(?:\s+(country|state|postalCode))?")
_FIRST_SEGMENT_RE = re.compile(r"^[A-Za-z0-9]+")
_XML_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

SARIF_RULES: list[dict[str, Any]] = [
    {
        "id": "FHIR001-Structural",
        "name": "StructuralValidation",
        "shortDescription": {"text": "FHIR R4 structural schema constraint violation"},
        "fullDescription": {
            "text": "The resource fails FHIR R4 structural schema validation or nesting limits."
        },
        "defaultConfiguration": {"level": "error"},
    },
    {
        "id": "FHIR002-Invariant",
        "name": "InvariantValidation",
        "shortDescription": {"text": "FHIR R4 FHIRPath invariant violation"},
        "fullDescription": {
            "text": "The resource violates a formal FHIRPath invariant (e.g. dom-6, pat-1, obs-7)."
        },
        "defaultConfiguration": {"level": "error"},
    },
    {
        "id": "FHIR003-Profile",
        "name": "ProfileValidation",
        "shortDescription": {"text": "Implementation Guide profile constraint violation"},
        "fullDescription": {
            "text": "The resource fails an IG StructureDefinition differential constraint."
        },
        "defaultConfiguration": {"level": "error"},
    },
    {
        "id": "FHIR004-Canadian",
        "name": "CanadianLocalization",
        "shortDescription": {"text": "Pan-Canadian baseline or CA-Core localization violation"},
        "fullDescription": {
            "text": "The resource fails Pan-Canadian baseline profile, JHN, or address rules."
        },
        "defaultConfiguration": {"level": "error"},
    },
    {
        "id": "FHIR005-ParseError",
        "name": "FileParseError",
        "shortDescription": {"text": "JSON syntax or file encoding parse error"},
        "fullDescription": {
            "text": "The input file could not be read or parsed as valid FHIR JSON/NDJSON."
        },
        "defaultConfiguration": {"level": "error"},
    },
    {
        "id": "FHIRLANCE_TERMINOLOGY",
        "name": "TerminologyValidation",
        "shortDescription": {"text": "FHIR R4 terminology or code system validation issue"},
        "fullDescription": {
            "text": "The resource fails code system, ValueSet binding, or grammar validation."
        },
        "defaultConfiguration": {"level": "error"},
    },
]

_RULE_INDEX_MAP: dict[str, int] = {rule["id"]: idx for idx, rule in enumerate(SARIF_RULES)}


def _sanitize_xml(text: str) -> str:
    return _XML_CONTROL_CHARS.sub("", text)


def _classify_issue_code(issue_str: str) -> str:
    stripped = _RE_NESTED_STRIP.sub("", issue_str)
    if stripped.startswith(_STRUCTURE_STARTS) or issue_str.startswith(_STRUCTURE_STARTS):
        return "structure"
    if "Invariant[" in issue_str or "ext-1" in issue_str:
        return "invariant"
    if (
        "not in required ValueSet" in issue_str
        or "Terminology[" in issue_str
        or "ValueSet" in issue_str
        or "CodeSystem" in issue_str
        or "grammar system" in issue_str
        or "could not validate code" in issue_str
    ):
        return "code-invalid"
    if (
        "missing required element" in issue_str
        or "missing Canadian" in issue_str
        or "no Canadian meta.profile" in issue_str
    ):
        return "required"
    if (
        "Profile[" in issue_str
        or "Address[" in issue_str
        or "Canadian" in issue_str
        or "US-only" in issue_str
    ):
        return "value"
    return "invalid"


def _extract_raw_path(issue_str: str) -> str:
    m_term = re.search(r"Terminology\[(.*?)\](?::|\s|$)", issue_str)
    if m_term:
        return m_term.group(1).strip()
    m_struct = _RE_STRUCTURAL_LOC.search(issue_str)
    if m_struct:
        raw_loc = m_struct.group(1).strip()
        return re.sub(r"\.(\d+)(?=\.|$)", r"[\1]", raw_loc)
    for pattern in (_RE_PROFILE_PATH, _RE_BARE_PATH, _RE_INVARIANT_PATH):
        m = pattern.search(issue_str)
        if m:
            return m.group(1).strip()
    m_addr = _RE_ADDRESS_PATH.search(issue_str)
    if m_addr:
        base = m_addr.group(1).lower()
        prop = m_addr.group(2)
        return f"{base}.{prop}" if prop else base
    return ""


def _extract_expression(issue_str: str, resource_type: str | None = None) -> list[str] | None:
    prefixes = _RE_NESTED_PREFIXES.findall(issue_str)
    prefix_path = ".".join(prefixes) if prefixes else ""
    inner_path = _extract_raw_path(issue_str)

    if prefix_path and inner_path:
        path = f"{prefix_path}.{inner_path}"
    elif prefix_path:
        path = prefix_path
    elif inner_path:
        path = inner_path
    else:
        return None

    first_segment = _FIRST_SEGMENT_RE.match(path)
    if first_segment and first_segment.group(0) in FHIR_RESOURCE_TYPES:
        return [path]

    if resource_type:
        return [f"{resource_type}.{path}"]
    return [path]


def _format_diagnostics(
    issue_str: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
) -> str:
    if resource_type and resource_id:
        target = f"{resource_type}/{resource_id}"
        if target not in issue_str:
            return f"{target}: {issue_str}"
        return issue_str
    if resource_type and resource_type not in issue_str:
        return f"{resource_type}: {issue_str}"
    return issue_str


def _build_outcome_issue(
    issue_str: str,
    *,
    resource_type: str | None = None,
    resource_id: str | None = None,
    severity: str = "error",
) -> dict[str, Any]:
    code = _classify_issue_code(issue_str)
    diag = _format_diagnostics(issue_str, resource_type=resource_type, resource_id=resource_id)
    expr = _extract_expression(issue_str, resource_type=resource_type)
    actual_severity = severity
    if severity == "error" and (
        issue_str.startswith("Warning: ") or "could not validate code" in issue_str
    ):
        actual_severity = "warning"
    item: dict[str, Any] = {
        "severity": actual_severity,
        "code": code,
        "diagnostics": diag,
    }
    if expr is not None and len(expr) > 0:
        item["expression"] = expr
    return item


def issues_to_operation_outcome(
    issues: list[str],
    *,
    resource_type: str | None = None,
    resource_id: str | None = None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    """Convert a list of validation issue strings to a valid FHIR R4 OperationOutcome."""
    outcomes: list[dict[str, Any]] = [
        _build_outcome_issue(
            issue_str,
            resource_type=resource_type,
            resource_id=resource_id,
            severity="error",
        )
        for issue_str in issues
    ]
    if warnings:
        outcomes.extend(
            _build_outcome_issue(
                warn_str,
                resource_type=resource_type,
                resource_id=resource_id,
                severity="warning",
            )
            for warn_str in warnings
        )
    if not outcomes:
        return {
            "resourceType": "OperationOutcome",
            "issue": [
                {
                    "severity": "information",
                    "code": "informational",
                    "diagnostics": "All OK - 0 validation issues found",
                }
            ],
        }
    return {
        "resourceType": "OperationOutcome",
        "issue": outcomes,
    }


def _infer_resource_type(entry: dict[str, Any]) -> str | None:
    declared = entry.get("resource_type") or entry.get("resourceType")
    if declared and str(declared) in FHIR_RESOURCE_TYPES:
        return str(declared)
    all_msgs = (entry.get("issues") or []) + (entry.get("warnings") or [])
    for issue in all_msgs:
        m = re.search(r"\bResource\s+([A-Z][a-zA-Z0-9]+)/", str(issue))
        if m and m.group(1) in FHIR_RESOURCE_TYPES:
            return m.group(1)
        m2 = re.search(r"\b([A-Z][a-zA-Z0-9]+)\.[a-zA-Z0-9]+", str(issue))
        if m2 and m2.group(1) in FHIR_RESOURCE_TYPES:
            return m2.group(1)
    file_stem = Path(str(entry.get("file", ""))).stem.capitalize()
    if file_stem in FHIR_RESOURCE_TYPES:
        return file_stem
    return None


def dataset_to_operation_outcome(report: dict[str, Any]) -> dict[str, Any]:
    """Convert a validate_dataset report dict into a single valid FHIR R4 OperationOutcome."""
    raw_issues: list[Any] = report.get("issues") or []
    raw_warnings: list[Any] = report.get("warnings") or []
    if not raw_issues and not raw_warnings:
        return issues_to_operation_outcome([])

    outcomes: list[dict[str, Any]] = []
    for entry in raw_issues:
        if isinstance(entry, str):
            outcomes.append(_build_outcome_issue(entry, severity="error"))
            continue
        if not isinstance(entry, dict):
            outcomes.append(_build_outcome_issue(str(entry), severity="error"))
            continue

        if "error" in entry:
            file_name = str(entry.get("file", "unknown"))
            line = entry.get("line")
            diag = (
                f"{file_name}:{line}: {entry['error']}"
                if line is not None
                else f"{file_name}: {entry['error']}"
            )
            outcomes.append(
                {
                    "severity": "error",
                    "code": "exception",
                    "diagnostics": diag,
                }
            )
        elif "issues" in entry:
            res_id = entry.get("id")
            res_type = _infer_resource_type(entry)
            sub_issues = entry.get("issues") or []
            outcomes.extend(
                _build_outcome_issue(
                    str(sub_issue),
                    resource_type=res_type,
                    resource_id=str(res_id) if res_id else None,
                    severity="error",
                )
                for sub_issue in sub_issues
            )

    for entry in raw_warnings:
        if isinstance(entry, dict) and "warnings" in entry:
            res_id = entry.get("id")
            res_type = _infer_resource_type(entry)
            sub_warns = entry.get("warnings") or []
            outcomes.extend(
                _build_outcome_issue(
                    str(sw),
                    resource_type=res_type,
                    resource_id=str(res_id) if res_id else None,
                    severity="warning",
                )
                for sw in sub_warns
            )

    if not outcomes:
        return issues_to_operation_outcome([])

    return {
        "resourceType": "OperationOutcome",
        "issue": outcomes,
    }


def _classify_sarif_rule_id(issue_str: str) -> str:
    if "Invariant[" in issue_str or "ext-1" in issue_str:
        return "FHIR002-Invariant"
    if (
        "no Canadian" in issue_str
        or "missing Canadian" in issue_str
        or "Canadian" in issue_str
        or "Address[" in issue_str
        or "US-only" in issue_str
    ):
        return "FHIR004-Canadian"
    if "Profile[" in issue_str or "not in required ValueSet" in issue_str:
        return "FHIR003-Profile"
    if (
        "Terminology[" in issue_str
        or "ValueSet" in issue_str
        or "CodeSystem" in issue_str
        or "grammar system" in issue_str
        or "could not validate code" in issue_str
    ):
        return "FHIRLANCE_TERMINOLOGY"
    return "FHIR001-Structural"


def _normalize_uri(file_name: str) -> str:
    norm = file_name.replace("\\", "/")
    if re.match(r"^[A-Za-z]:/", norm):
        return f"file:///{norm}"
    return norm


def _build_sarif_location(file_name: str, line_no: int | None) -> dict[str, Any]:
    loc: dict[str, Any] = {
        "physicalLocation": {"artifactLocation": {"uri": _normalize_uri(file_name)}}
    }
    if line_no is not None and line_no > 0:
        loc["physicalLocation"]["region"] = {"startLine": line_no}
    return loc


def dataset_to_sarif(report: dict[str, Any]) -> dict[str, Any]:
    """Convert a validate_dataset report dict into standard SARIF v2.1.0 JSON."""
    raw_issues: list[Any] = report.get("issues") or []
    results: list[dict[str, Any]] = []

    for entry in raw_issues:
        if isinstance(entry, str):
            rule_id = _classify_sarif_rule_id(entry)
            rule_index = _RULE_INDEX_MAP.get(rule_id, 0)
            results.append(
                {
                    "ruleId": rule_id,
                    "ruleIndex": rule_index,
                    "level": "error",
                    "message": {"text": str(entry or "Validation error")},
                    "locations": [_build_sarif_location("unknown", None)],
                }
            )
            continue
        if not isinstance(entry, dict):
            rule_id = _classify_sarif_rule_id(str(entry))
            rule_index = _RULE_INDEX_MAP.get(rule_id, 0)
            results.append(
                {
                    "ruleId": rule_id,
                    "ruleIndex": rule_index,
                    "level": "error",
                    "message": {"text": str(entry or "Validation error")},
                    "locations": [_build_sarif_location("unknown", None)],
                }
            )
            continue

        file_name = str(entry.get("file", "unknown"))
        line_no = entry.get("line")
        loc = _build_sarif_location(file_name, line_no)

        if "error" in entry:
            rule_id = "FHIR005-ParseError"
            rule_index = _RULE_INDEX_MAP[rule_id]
            results.append(
                {
                    "ruleId": rule_id,
                    "ruleIndex": rule_index,
                    "level": "error",
                    "message": {"text": str(entry.get("error") or "Validation error")},
                    "locations": [loc],
                }
            )
        elif "issues" in entry:
            for issue_str in entry.get("issues") or []:
                rule_id = _classify_sarif_rule_id(str(issue_str))
                rule_index = _RULE_INDEX_MAP[rule_id]
                results.append(
                    {
                        "ruleId": rule_id,
                        "ruleIndex": rule_index,
                        "level": "error",
                        "message": {"text": str(issue_str or "Validation error")},
                        "locations": [loc],
                    }
                )

    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "FHIRlance",
                        "version": "0.1.0",
                        "informationUri": "https://github.com/damsonaldson/FHIRlance",
                        "rules": SARIF_RULES,
                    }
                },
                "results": results,
            }
        ],
    }


def _append_junit_failure_testcase(suite: ET.Element, entry: dict[str, Any]) -> None:
    file_name = _sanitize_xml(str(entry.get("file", "unknown")))
    line = entry.get("line")
    base_file = Path(file_name).name

    if "error" in entry:
        err_msg = _sanitize_xml(str(entry["error"]))
        tc_name = f"parse_{base_file}" if line is None else f"parse_{base_file}_line_{line}"
        tc = ET.SubElement(
            suite,
            "testcase",
            attrib={"classname": file_name, "name": tc_name, "time": "0.0000"},
        )
        fail = ET.SubElement(
            tc,
            "failure",
            attrib={"message": err_msg[:120], "type": "ParseError"},
        )
        fail.text = err_msg
        return

    res_id = _sanitize_xml(str(entry.get("id") or "unidentified_resource"))
    issues: list[str] = [_sanitize_xml(str(i)) for i in (entry.get("issues") or [])]
    tc_name = f"validate_{res_id}" if line is None else f"validate_{res_id}_line_{line}"
    tc = ET.SubElement(
        suite,
        "testcase",
        attrib={"classname": file_name, "name": tc_name, "time": "0.0000"},
    )
    first_issue = issues[0] if issues else "Validation error"
    fail = ET.SubElement(
        tc,
        "failure",
        attrib={"message": first_issue[:120], "type": "ValidationError"},
    )
    fail.text = "\n".join(issues)


def dataset_to_junit_xml(report: dict[str, Any]) -> str:
    """Convert a validate_dataset report dict into a valid JUnit XML string."""
    elapsed = float(report.get("elapsed_seconds") or 0.0)
    valid_count = int(report.get("valid_resources") or 0)
    raw_issues: list[Any] = report.get("issues") or []
    failures_count = len(raw_issues)

    has_valid_case = valid_count > 0 or failures_count == 0
    total_tests = failures_count + (1 if has_valid_case else 0)

    root = ET.Element(
        "testsuites",
        attrib={
            "name": "FHIRlance Validation",
            "tests": str(total_tests),
            "failures": str(failures_count),
            "errors": "0",
            "time": f"{elapsed:.4f}",
        },
    )
    suite = ET.SubElement(
        root,
        "testsuite",
        attrib={
            "name": "FHIRlance",
            "tests": str(total_tests),
            "failures": str(failures_count),
            "errors": "0",
            "time": f"{elapsed:.4f}",
        },
    )

    if valid_count > 0:
        ET.SubElement(
            suite,
            "testcase",
            attrib={
                "classname": "FHIRlance",
                "name": f"valid_resources ({valid_count})",
                "time": "0.0000",
            },
        )
    elif failures_count == 0:
        ET.SubElement(
            suite,
            "testcase",
            attrib={
                "classname": "FHIRlance",
                "name": "valid_dataset (0 resources)",
                "time": "0.0000",
            },
        )

    for entry in raw_issues:
        dict_entry = (
            entry if isinstance(entry, dict) else {"file": "unknown", "issues": [str(entry)]}
        )
        _append_junit_failure_testcase(suite, dict_entry)

    xml_bytes = ET.tostring(root, encoding="utf-8")
    return f'<?xml version="1.0" encoding="utf-8"?>\n{xml_bytes.decode("utf-8")}\n'


def _format_text_report(report: dict[str, Any], max_displayed_issues: int) -> str:
    elapsed = float(report.get("elapsed_seconds") or 0.0)
    total = int(report.get("total_resources") or 0)
    valid = int(report.get("valid_resources") or 0)
    invalid = int(report.get("invalid_resources") or max(0, total - valid))
    compliance = float(
        report.get("compliance_rate") or ((valid / total * 100.0) if total > 0 else 0.0)
    )

    lines = [
        f"Validated {total} resource(s) in {elapsed:.4f}s | "
        f"valid={valid} invalid={invalid} ({compliance:.2f}%)"
    ]
    raw_issues: list[Any] = report.get("issues") or []
    lines.extend(f"  - {item}" for item in raw_issues[:max_displayed_issues])
    return "\n".join(lines)


def format_dataset_report(
    report: dict[str, Any],
    output_format: str = "text",
    *,
    max_displayed_issues: int = 20,
) -> str:
    """Format a validate_dataset report dictionary into the requested output format."""
    normalized_format = output_format.strip().lower()
    if normalized_format == "text":
        return _format_text_report(report, max_displayed_issues)
    if normalized_format == "json":
        return json.dumps(report, indent=2)
    if normalized_format == "operation-outcome":
        return json.dumps(dataset_to_operation_outcome(report), indent=2)
    if normalized_format == "sarif":
        return json.dumps(dataset_to_sarif(report), indent=2)
    if normalized_format == "junit":
        return dataset_to_junit_xml(report)

    raise ValueError(
        f"Unknown output format: {output_format!r}. Supported formats: {SUPPORTED_OUTPUT_FORMATS}"
    )


def validate_to_operation_outcome(
    resource: Any,
    *,
    require_canadian_profile: bool = True,
    profile_urls: list[str] | None = None,
    ig_sources: Sequence[str | Path] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Validate a single resource and return a valid FHIR R4 OperationOutcome."""
    warnings: list[str] = []
    issues = validate_resource(
        resource,
        require_canadian_profile=require_canadian_profile,
        profile_urls=profile_urls,
        ig_sources=ig_sources,
        _warnings_out=warnings,
        **kwargs,
    )
    res_type = resource.get("resourceType") if isinstance(resource, dict) else None
    res_id = resource.get("id") if isinstance(resource, dict) else None
    return issues_to_operation_outcome(
        issues,
        resource_type=str(res_type) if res_type else None,
        resource_id=str(res_id) if res_id else None,
        warnings=warnings,
    )


__all__ = [
    "FHIR_RESOURCE_TYPES",
    "SARIF_RULES",
    "SUPPORTED_OUTPUT_FORMATS",
    "dataset_to_junit_xml",
    "dataset_to_operation_outcome",
    "dataset_to_sarif",
    "format_dataset_report",
    "issues_to_operation_outcome",
    "validate_to_operation_outcome",
]
