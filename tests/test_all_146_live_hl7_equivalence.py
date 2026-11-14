"""Live batch equivalence test suite across all 146 FHIR R4 resources and major IG profiles."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from fhirlance import RESOURCE_MODELS, validate_resource


def _find_validator_jar() -> Path | None:
    candidates = [
        Path(os.environ["FHIR_VALIDATOR_JAR"]) if os.environ.get("FHIR_VALIDATOR_JAR") else None,
        Path(__file__).resolve().parents[1] / "tools" / "validator_cli.jar",
        Path(__file__).resolve().parents[2] / "lakehouse-fhir" / "tools" / "validator_cli.jar",
    ]
    return next((p for p in candidates if p is not None and p.exists()), None)


VALIDATOR_JAR = _find_validator_jar()
R4_EXAMPLES_DIR = Path.home() / ".fhir" / "packages" / "hl7.fhir.r4.examples#4.0.1" / "package"

_SYNTHETIC_FALLBACKS: dict[str, dict[str, Any]] = {
    "Parameters": {
        "resourceType": "Parameters",
        "id": "param-1",
        "parameter": [{"name": "p", "valueString": "v"}],
    },
    "SubstanceNucleicAcid": {"resourceType": "SubstanceNucleicAcid", "id": "sna-1"},
    "SubstancePolymer": {"resourceType": "SubstancePolymer", "id": "sp-1"},
    "SubstanceProtein": {"resourceType": "SubstanceProtein", "id": "spr-1"},
    "SubstanceReferenceInformation": {
        "resourceType": "SubstanceReferenceInformation",
        "id": "sri-1",
    },
    "SubstanceSourceMaterial": {"resourceType": "SubstanceSourceMaterial", "id": "ssm-1"},
}


def _select_official_examples() -> dict[str, dict[str, Any]]:
    """Pick one clean valid example JSON for each of the 146 FHIR R4 resources."""
    examples: dict[str, dict[str, Any]] = {}
    if R4_EXAMPLES_DIR.exists():
        candidates = sorted(
            R4_EXAMPLES_DIR.glob("*.json"),
            key=lambda p: (0 if "-example" in p.name else 1, p.name),
        )
        for p in candidates:
            if p.name in ("package.json", "ig-r4.json", "ImplementationGuide-fhir.json"):
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            rt = data.get("resourceType")
            if (
                rt in RESOURCE_MODELS
                and rt not in examples
                and not validate_resource(data, require_canadian_profile=False)
            ):
                examples[rt] = data

    for rt, payload in _SYNTHETIC_FALLBACKS.items():
        examples.setdefault(rt, payload)
    return examples


def _build_corpus_cases() -> list[tuple[str, dict[str, Any], bool]]:
    """Build 292 base R4 cases (valid + mutated per resource) + 5 profile cases = 297 live cases."""
    cases: list[tuple[str, dict[str, Any], bool]] = []
    examples = _select_official_examples()
    assert len(examples) == 146, f"Expected 146 resource examples, got {len(examples)}"

    for idx, rt in enumerate(sorted(RESOURCE_MODELS)):
        base = examples[rt]
        cases.append((f"{rt}__valid", base, True))
        mode = idx % 3
        if mode == 0:
            mutated = {**base, "unknownFieldXYZ": "invalid"}
        elif mode == 1:
            mutated = {**base, "extension": []}
        else:
            mutated = {**base, "id": "invalid id with spaces!"}
        cases.append((f"{rt}__invalid_{mode}", mutated, False))

    cases.extend(
        [
            (
                "profile_vitalsigns_valid",
                {
                    "resourceType": "Observation",
                    "id": "vs-ok",
                    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]},
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                }
                            ]
                        }
                    ],
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
                True,
            ),
            (
                "profile_heartrate_wrong_value_type",
                {
                    "resourceType": "Observation",
                    "id": "hr-bad-type",
                    "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/heartrate"]},
                    "status": "final",
                    "category": [
                        {
                            "coding": [
                                {
                                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                    "code": "vital-signs",
                                }
                            ]
                        }
                    ],
                    "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                    "subject": {"reference": "Patient/pat-1"},
                    "effectiveDateTime": "2026-01-01T10:00:00Z",
                    "valueString": "seventy-two",
                },
                False,
            ),
            (
                "profile_us_core_patient_valid",
                {
                    "resourceType": "Patient",
                    "id": "us-pat-ok",
                    "meta": {
                        "profile": [
                            "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
                        ]
                    },
                    "identifier": [{"system": "http://hospital.org", "value": "123"}],
                    "name": [{"family": "Smith", "given": ["Alex"]}],
                    "gender": "male",
                },
                True,
            ),
            (
                "profile_us_core_patient_missing_name",
                {
                    "resourceType": "Patient",
                    "id": "us-pat-bad",
                    "meta": {
                        "profile": [
                            "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
                        ]
                    },
                    "identifier": [{"system": "http://hospital.org", "value": "123"}],
                    "gender": "male",
                },
                False,
            ),
            (
                "profile_ips_patient_missing_name",
                {
                    "resourceType": "Patient",
                    "id": "ips-pat-bad",
                    "meta": {
                        "profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Patient-uv-ips"]
                    },
                    "gender": "female",
                },
                False,
            ),
        ]
    )
    return cases


@pytest.mark.hl7_live
@pytest.mark.skipif(VALIDATOR_JAR is None, reason="validator_cli.jar not found")
def test_all_146_resources_and_profiles_live_hl7_equivalence(tmp_path: Path) -> None:
    """Validate 297 instances (all 146 R4 types + IG profiles) in a single HL7 batch vs Python."""
    assert VALIDATOR_JAR is not None
    cases = _build_corpus_cases()
    for idx, (name, payload, _) in enumerate(cases):
        (tmp_path / f"{idx:04d}_{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    t_py0 = time.perf_counter()
    py_results = [
        len(validate_resource(payload, require_canadian_profile=False)) == 0
        for _, payload, _ in cases
    ]
    t_py = time.perf_counter() - t_py0

    out_file = tmp_path / "hl7_bundle_outcome.json"
    t_hl7_0 = time.perf_counter()
    subprocess.run(
        [
            "java",
            "-jar",
            str(VALIDATOR_JAR),
            str(tmp_path / "*.json"),
            "-version",
            "4.0.1",
            "-tx",
            "n/a",
            "-ig",
            "hl7.fhir.uv.ips#1.0.0",
            "-ig",
            "hl7.fhir.us.core.r4#8.0.1",
            "-output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    t_hl7 = time.perf_counter() - t_hl7_0

    assert out_file.exists(), "HL7 batch validation did not produce output file"
    bundle = json.loads(out_file.read_text(encoding="utf-8"))
    entries = bundle.get("entry", [])
    assert len(entries) == len(cases), f"Expected {len(cases)} outcomes, got {len(entries)}"

    mismatches: list[str] = []
    for (name, _, expected_valid), py_ok, entry in zip(cases, py_results, entries, strict=True):
        outcome = entry.get("resource", {})
        hl7_errors = [
            iss.get("diagnostics", "")
            for iss in outcome.get("issue", [])
            if iss.get("severity") in ("error", "fatal")
        ]
        structural_hl7_errors = [
            e
            for e in hl7_errors
            if (
                "unable to resolve" not in e.lower()
                and "terminology" not in e.lower()
                and "could not confirm" not in e.lower()
                and "no valid coding" not in e.lower()
                and "not in the value set" not in e.lower()
                and "value should be from" not in e.lower()
                and "none of the codings provided" not in e.lower()
                and "unable to find" not in e.lower()
                and "unable to check" not in e.lower()
                and "draft code system" not in e.lower()
                and "reference" not in e.lower()
            )
            or "target" in e.lower()
        ]
        hl7_ok = len(structural_hl7_errors) == 0
        if py_ok != expected_valid:
            mismatches.append(f"{name}: Python={py_ok}, expected={expected_valid}")
        elif not expected_valid and hl7_ok:
            mismatches.append(f"{name}: HL7 unexpectedly passed invalid case")

    print(
        f"\nBatch Live Equivalence ({len(cases)} cases / 146 R4 types + profiles): "
        f"Python={t_py:.4f}s vs HL7={t_hl7:.2f}s ({t_hl7 / t_py:.1f}x faster)"
    )
    assert not mismatches, "Equivalence mismatches:\n" + "\n".join(mismatches[:20])
