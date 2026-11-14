"""Comprehensive tests: FHIR R4 edge cases, multi-IG profiles, CLI, and resilience."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fhirlance import loads_strict_json, validate_dataset, validate_resource
from fhirlance.cli import main as cli_main


def _valid_ca_patient() -> dict[str, Any]:
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
                "system": "https://fhir.infoway-inforoute.ca/NamingSystem/ca-ns-patient-health-card-number",
                "value": "1234567890",
            }
        ],
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "telecom": [{"system": "phone", "value": "902-555-0100"}],
        "gender": "female",
        "birthDate": "1990-05-15",
        "address": [{"city": "Dartmouth", "state": "NS", "postalCode": "B2Y 1A1", "country": "CA"}],
    }


@pytest.mark.parametrize(
    "bad_resource",
    [
        {},
        {"resourceType": "Patient", "id": "p1"},
        {**_valid_ca_patient(), "meta": {}},
        {**_valid_ca_patient(), "identifier": [{"system": "http://x.org", "value": "1"}]},
        {
            **_valid_ca_patient(),
            "address": [{"country": "US", "state": "NS", "postalCode": "B2Y 1A1"}],
        },
        {
            **_valid_ca_patient(),
            "address": [{"country": "CA", "state": "ZZ", "postalCode": "B2Y 1A1"}],
        },
        {
            **_valid_ca_patient(),
            "address": [{"country": "CA", "state": "NS", "postalCode": "12345"}],
        },
        {
            **_valid_ca_patient(),
            "extension": [
                {
                    "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
                    "valueString": "x",
                }
            ],
        },
    ],
)
def test_canadian_profile_rules_enforced(bad_resource: dict[str, Any]) -> None:
    """Canadian profile presence, JHN, address, and disallowed US extensions are flagged."""
    assert validate_resource(bad_resource)


def test_primitive_extensions_valid_and_invalid() -> None:
    p = _valid_ca_patient()
    p["_birthDate"] = {"extension": [{"url": "http://example.org/ext", "valueString": "approx"}]}
    p["name"][0]["_given"] = [None]
    assert validate_resource(p) == []

    p_bad_field = {**_valid_ca_patient(), "_notARealField": {"id": "1"}}
    assert any("Structural[" in i for i in validate_resource(p_bad_field))

    p_bad_ext = {**_valid_ca_patient(), "_birthDate": {"bogus": 1}}
    assert any("Structural[" in i for i in validate_resource(p_bad_ext))


def test_extension_ext1_invariant_and_meta_narrative_strictness() -> None:
    p1 = {**_valid_ca_patient(), "extension": [{"url": "http://example.org/empty"}]}
    assert any("ext-1" in i for i in validate_resource(p1))

    p2 = {
        **_valid_ca_patient(),
        "extension": [
            {
                "url": "http://example.org/both",
                "valueString": "x",
                "extension": [{"url": "sub", "valueString": "y"}],
            }
        ],
    }
    assert any("ext-1" in i for i in validate_resource(p2))

    p3 = {
        **_valid_ca_patient(),
        "meta": {"profile": [_valid_ca_patient()["meta"]["profile"][0]], "badKey": 1},
    }
    assert any("Structural[" in i for i in validate_resource(p3))

    p4 = {**_valid_ca_patient(), "text": {"status": "bad-status", "div": "<div>hi</div>"}}
    assert any("Structural[" in i for i in validate_resource(p4))


def test_observation_obs7_and_bundle_recursive_and_bdl7() -> None:
    obs_bad = {
        "resourceType": "Observation",
        "meta": {
            "profile": ["http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-observation"]
        },
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9"}]},
        "valueQuantity": {"value": 120, "unit": "mmHg"},
        "component": [{"code": {"coding": [{"system": "http://loinc.org", "code": "85354-9"}]}}],
    }
    assert any("obs-7" in i for i in validate_resource(obs_bad))

    bundle_bad = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"fullUrl": "urn:uuid:dup", "resource": {"resourceType": "Patient", "unknown": 1}},
            {"fullUrl": "urn:uuid:dup", "resource": _valid_ca_patient()},
        ],
    }
    issues = validate_resource(bundle_bad, require_canadian_profile=False)
    assert any("bdl-7" in i for i in issues)
    assert any("entry[0].resource:" in i for i in issues)


def test_contained_resource_recursive_validation() -> None:
    p = {**_valid_ca_patient(), "contained": [{"resourceType": "Organization", "bogusField": True}]}
    issues = validate_resource(p)
    assert any("contained[0]:" in i and "Structural[" in i for i in issues)


def test_ca_baseline_vitalsigns_ips_and_us_core_profiles() -> None:
    p_no_sys = _valid_ca_patient()
    p_no_sys["telecom"] = [{"value": "902-555-0100"}]
    assert any("Patient.telecom.system" in i for i in validate_resource(p_no_sys))

    obs_vitals_missing_cat = {
        "resourceType": "Observation",
        "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]},
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "subject": {"reference": "Patient/pat-1"},
        "effectiveDateTime": "2026-01-01T10:00:00Z",
        "valueQuantity": {"value": 72, "unit": "beats/min"},
    }
    assert any(
        "Observation.category" in i
        for i in validate_resource(obs_vitals_missing_cat, require_canadian_profile=False)
    )

    ips_patient_no_name = {
        "resourceType": "Patient",
        "meta": {"profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Patient-uv-ips"]},
        "gender": "female",
    }
    assert any(
        "Patient.name" in i
        for i in validate_resource(ips_patient_no_name, require_canadian_profile=False)
    )

    us_patient_ok = {
        "resourceType": "Patient",
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]},
        "identifier": [{"system": "http://hospital.org", "value": "123"}],
        "name": [{"family": "Smith", "given": ["Alex"]}],
        "gender": "male",
    }
    assert validate_resource(us_patient_ok, require_canadian_profile=False) == []

    wrong_type = {
        "resourceType": "Observation",
        "meta": {"profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]},
        "status": "final",
        "code": {"text": "HR"},
    }
    assert any(
        "profile applies to 'Patient', got 'Observation'" in i
        for i in validate_resource(wrong_type, require_canadian_profile=False)
    )


def test_resilience_and_cli(tmp_path: Path) -> None:
    bad_inputs: tuple[Any, ...] = (None, [], "Patient", 42)
    for bad in bad_inputs:
        issues = validate_resource(bad)
        assert len(issues) == 1
        assert "JSON object" in issues[0]

    with pytest.raises(ValueError, match="non-standard JSON"):
        loads_strict_json('{"resourceType": "Observation", "value": NaN}')

    nested: dict[str, Any] = {"resourceType": "Bundle", "type": "collection"}
    cur = nested
    for _ in range(20):
        nxt: dict[str, Any] = {"resourceType": "Bundle", "type": "collection"}
        cur["entry"] = [{"resource": nxt}]
        cur = nxt
    assert any(
        "Maximum resource nesting depth" in i
        for i in validate_resource(nested, require_canadian_profile=False)
    )

    good_ndjson = tmp_path / "mixed.ndjson"
    good_ndjson.write_text(
        json.dumps(_valid_ca_patient())
        + "\n"
        + "{not valid json\n"
        + '{"resourceType": "Patient", "x": NaN}\n'
        + "[1, 2, 3]\n",
        encoding="utf-8",
    )
    res = validate_dataset(tmp_path)
    assert res["total_resources"] == 4
    assert res["valid_resources"] == 1
    assert res["invalid_resources"] == 3

    valid_json = tmp_path / "extra.json"
    valid_json.write_text(json.dumps(_valid_ca_patient()), encoding="utf-8")
    res_par = validate_dataset(tmp_path, parallel=True)
    assert res_par["total_resources"] == 5
    assert res_par["valid_resources"] == 2
    assert cli_main([str(valid_json)]) == 0
    assert cli_main([str(good_ndjson), "--json"]) == 1
