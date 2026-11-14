"""Comparative test suite evaluating FHIRlance against HL7's official validator_cli.jar."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest

from fhirlance import validate_resource


def _find_validator_jar() -> Path | None:
    candidates = [
        Path(os.environ["FHIR_VALIDATOR_JAR"]) if os.environ.get("FHIR_VALIDATOR_JAR") else None,
        Path(__file__).resolve().parents[1] / "tools" / "validator_cli.jar",
        Path(__file__).resolve().parents[2] / "lakehouse-fhir" / "tools" / "validator_cli.jar",
    ]
    return next((p for p in candidates if p is not None and p.exists()), None)


VALIDATOR_JAR = _find_validator_jar()


def run_hl7_validator(resource: dict[str, Any], tmp_path: Path) -> list[str]:
    """Run HL7 validator_cli.jar on a single resource and return error/fatal messages."""
    assert VALIDATOR_JAR is not None
    in_file = tmp_path / "resource.json"
    out_file = tmp_path / "outcome.json"
    in_file.write_text(json.dumps(resource), encoding="utf-8")

    subprocess.run(
        [
            "java",
            "-jar",
            str(VALIDATOR_JAR),
            str(in_file),
            "-version",
            "4.0.1",
            "-tx",
            "n/a",
            "-output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if not out_file.exists():
        return ["HL7 validator failed to produce OperationOutcome"]

    outcome = json.loads(out_file.read_text(encoding="utf-8"))
    return [
        issue.get("diagnostics") or issue.get("details", {}).get("text", "Unknown error")
        for issue in outcome.get("issue", [])
        if issue.get("severity") in ("error", "fatal")
    ]


def _base_valid_canadian_patient() -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "pat-1",
        "meta": {
            "profile": ["http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient"]
        },
        "identifier": [
            {
                "type": {
                    "coding": [
                        {"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "JHN"}
                    ]
                },
                "system": "http://ns.ca/jhn",
                "value": "1234567890",
            }
        ],
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1990-05-15",
        "address": [{"city": "Dartmouth", "state": "NS", "postalCode": "B2Y 1A1", "country": "CA"}],
    }


@pytest.mark.hl7_live
@pytest.mark.skipif(VALIDATOR_JAR is None, reason="validator_cli.jar not found")
@pytest.mark.parametrize(
    ("name", "mutator", "expect_py_valid", "expect_hl7_valid"),
    [
        ("valid_canadian_patient", lambda p: p, True, True),
        ("unknown_property", lambda p: {**p, "unknownField": "oops"}, False, False),
        ("wrong_type_birthdate", lambda p: {**p, "birthDate": 19900515}, False, False),
        ("invalid_date_format", lambda p: {**p, "birthDate": "1990-13-45"}, False, False),
        ("invalid_gender_code", lambda p: {**p, "gender": "not-a-fhir-code"}, False, False),
        (
            "fhirpath_pat_1_violation",
            lambda p: {**p, "contact": [{"gender": "male"}]},
            False,
            False,
        ),
        (
            "unknown_resource_type",
            lambda _: {"resourceType": "FakeResource", "id": "1"},
            False,
            False,
        ),
        ("empty_array", lambda p: {**p, "telecom": []}, False, False),
        (
            "missing_ca_jhn",
            lambda p: {k: v for k, v in p.items() if k != "identifier"},
            False,
            True,
        ),
        (
            "vitalsigns_profile_missing_category",
            lambda _: {
                "resourceType": "Observation",
                "id": "obs-vs-1",
                "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]},
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "subject": {"reference": "Patient/pat-1"},
                "effectiveDateTime": "2026-01-01T10:00:00Z",
                "valueQuantity": {
                    "value": 72,
                    "unit": "beats/min",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min",
                },
            },
            False,
            False,
        ),
    ],
)
def test_validator_equivalence(
    name: str,
    mutator: Any,
    expect_py_valid: bool,
    expect_hl7_valid: bool,
    tmp_path: Path,
) -> None:
    """Compare Python validator vs HL7 validator across structural and profile cases."""
    resource = mutator(_base_valid_canadian_patient())
    py_issues = validate_resource(resource)
    hl7_errors = run_hl7_validator(resource, tmp_path)

    assert (len(py_issues) == 0) == expect_py_valid, f"[{name}] Python mismatch: issues={py_issues}"
    assert (len(hl7_errors) == 0) == expect_hl7_valid, f"[{name}] HL7 mismatch: errors={hl7_errors}"
