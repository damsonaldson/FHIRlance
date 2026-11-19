"""Regression tests for real-world Ontario Health DHDR & Medical Imaging IG findings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fhirlance import (
    RESOURCE_MODELS,
    TxOptions,
    load_compiled_ig_profiles,
    register_ig,
    validate_binding_value,
    validate_resource,
)
from fhirlance.extensions import compile_extensions, validate_extensions
from fhirlance.ig_loader import clear_ig_cache
from fhirlance.profile_engine import COMPILED_PROFILES
from fhirlance.terminology import is_valid_ucum_code


def test_register_ig_and_load_profiles_accept_single_str_or_path(tmp_path: Path) -> None:
    sd_path = tmp_path / "sd-custom.json"
    sd_path.write_text(
        json.dumps(
            {
                "resourceType": "StructureDefinition",
                "url": "http://example.org/StructureDefinition/single-path-patient",
                "name": "SinglePathPatient",
                "status": "active",
                "kind": "resource",
                "abstract": False,
                "type": "Patient",
                "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
                "derivation": "constraint",
                "snapshot": {
                    "element": [
                        {"id": "Patient", "path": "Patient", "min": 0, "max": "*"},
                        {"id": "Patient.name", "path": "Patient.name", "min": 1, "max": "*"},
                    ]
                },
            }
        ),
        encoding="utf-8",
    )

    loaded_from_str = load_compiled_ig_profiles(str(sd_path))
    assert "http://example.org/StructureDefinition/single-path-patient" in loaded_from_str

    loaded_from_path = load_compiled_ig_profiles(sd_path)
    assert "http://example.org/StructureDefinition/single-path-patient" in loaded_from_path

    url = "http://example.org/StructureDefinition/single-path-patient"
    try:
        registered = register_ig(str(sd_path))
        assert url in registered
    finally:
        COMPILED_PROFILES.pop(url, None)
        clear_ig_cache()


def test_extension_context_element_canonical_and_profile_qualified() -> None:
    compiled = compile_extensions(
        {
            "http://example.org/ext-element": {
                "url": "http://example.org/ext-element",
                "is_modifier": False,
                "contexts": [("element", "Element")],
                "node": {"url": "http://example.org/ext-element", "value_types": ["code"]},
            },
            "http://example.org/ext-canonical": {
                "url": "http://example.org/ext-canonical",
                "is_modifier": False,
                "contexts": [("element", "CanonicalResource")],
                "node": {"url": "http://example.org/ext-canonical", "value_types": ["code"]},
            },
            "http://example.org/ext-profile-qualified": {
                "url": "http://example.org/ext-profile-qualified",
                "is_modifier": False,
                "contexts": [
                    (
                        "element",
                        "http://ontariohealth.ca/fhir/StructureDefinition/ca-on-profile-ServiceRequest#ServiceRequest",
                    )
                ],
                "node": {
                    "url": "http://example.org/ext-profile-qualified",
                    "value_types": ["string"],
                },
            },
        }
    )

    vs_resource: dict[str, Any] = {
        "resourceType": "ValueSet",
        "status": "active",
        "extension": [
            {"url": "http://example.org/ext-canonical", "valueCode": "normative"},
        ],
        "compose": {
            "include": [
                {
                    "system": "http://example.org/cs",
                    "extension": [{"url": "http://example.org/ext-element", "valueCode": "vocab"}],
                }
            ]
        },
    }
    assert (
        validate_extensions(
            vs_resource, RESOURCE_MODELS["ValueSet"], "ValueSet", compiled_extensions=compiled
        )
        == []
    )

    sr_resource: dict[str, Any] = {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "subject": {"reference": "Patient/1"},
        "extension": [
            {"url": "http://example.org/ext-profile-qualified", "valueString": "copied"},
        ],
    }
    assert (
        validate_extensions(
            sr_resource,
            RESOURCE_MODELS["ServiceRequest"],
            "ServiceRequest",
            compiled_extensions=compiled,
        )
        == []
    )

    # CanonicalResource should NOT match a non-canonical resource like Patient
    pat_resource: dict[str, Any] = {
        "resourceType": "Patient",
        "extension": [{"url": "http://example.org/ext-canonical", "valueCode": "normative"}],
    }
    issues = validate_extensions(
        pat_resource, RESOURCE_MODELS["Patient"], "Patient", compiled_extensions=compiled
    )
    assert any("not valid in context 'Patient'" in i for i in issues)


def test_extensible_binding_valid_complete_system_code_is_warning_not_error() -> None:
    # v2-0203#VN (Visit Number) is a valid code in v2-0203 extending identifier-type
    encounter: dict[str, Any] = {
        "resourceType": "Encounter",
        "status": "finished",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "IMP",
        },
        "identifier": [
            {
                "type": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/v2-0203",
                            "code": "VN",
                        }
                    ]
                },
                "value": "ENC-123",
            }
        ],
    }
    warnings: list[str] = []
    issues = validate_resource(encounter, tx="local", _warnings_out=warnings)
    assert issues == []
    assert any("not in extensible ValueSet" in w for w in warnings)

    strict_issues = validate_resource(encounter, tx=TxOptions(mode="local", strict_extensible=True))
    assert any("not in extensible ValueSet" in i for i in strict_issues)


def test_unexpanded_empty_vs_spec_does_not_reject_in_local_mode() -> None:
    empty_spec: dict[str, Any] = {
        "codes": frozenset(),
        "system_codes": {},
        "external_systems": (),
    }
    res = validate_binding_value(
        {"system": "http://snomed.info/sct", "code": "428673006"},
        "MedicationDispense.extension[0].valueQuantity",
        "https://fhir.infoway-inforoute.ca/ValueSet/unexpanded-stub",
        "required",
        TxOptions(mode="local"),
        vs_spec=empty_spec,
    )
    assert res.errors == []


def test_ucum_british_imperial_and_yard_units_valid() -> None:
    for code in ("[foz_br]", "[gal_br]", "[pt_br]", "[qt_br]", "[syd_i]", "[cyd_i]"):
        assert is_valid_ucum_code(code), f"Expected UCUM code {code!r} to be valid"
