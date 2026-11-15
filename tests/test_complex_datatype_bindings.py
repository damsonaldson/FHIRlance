"""Tests for Tier 1 #4: Complex Datatype Element Bindings."""

from __future__ import annotations

from typing import Any

from fhirlance.profile_engine import CompiledBindingRule, CompiledProfile
from fhirlance.profiles import COMPLEX_TYPE_BINDINGS
from fhirlance.resource_validator import validate_resource


def test_complex_type_bindings_table_and_literal_exclusions() -> None:
    expected_types = {
        "Identifier",
        "Meta",
        "UsageContext",
        "Expression",
        "Reference",
        "Money",
        "Attachment",
        "DataRequirement",
        "ElementDefinition",
        "ParameterDefinition",
        "Signature",
    }
    assert expected_types.issubset(COMPLEX_TYPE_BINDINGS.keys())
    assert "type" in COMPLEX_TYPE_BINDINGS["Identifier"]
    assert "security" in COMPLEX_TYPE_BINDINGS["Meta"]
    assert "code" in COMPLEX_TYPE_BINDINGS["UsageContext"]
    assert "language" in COMPLEX_TYPE_BINDINGS["Expression"]
    assert "type" in COMPLEX_TYPE_BINDINGS["Reference"]
    assert "currency" in COMPLEX_TYPE_BINDINGS["Money"]
    assert "contentType" in COMPLEX_TYPE_BINDINGS["Attachment"]
    assert "subjectCodeableConcept" in COMPLEX_TYPE_BINDINGS["DataRequirement"]

    # Literal[...] bindings in types.py must remain excluded from COMPLEX_TYPE_BINDINGS
    # and continue to be enforced structurally by Pydantic.
    assert "Address" not in COMPLEX_TYPE_BINDINGS
    assert "ContactPoint" not in COMPLEX_TYPE_BINDINGS
    assert "HumanName" not in COMPLEX_TYPE_BINDINGS
    assert "use" not in COMPLEX_TYPE_BINDINGS["Identifier"]

    patient_bad_literals: dict[str, Any] = {
        "resourceType": "Patient",
        "identifier": [{"use": "bogus-use", "value": "123"}],
        "name": [{"use": "bogus-name-use", "family": "Doe"}],
        "telecom": [{"system": "bogus-system", "value": "555-1234"}],
        "address": [{"use": "bogus-addr-use", "city": "Toronto"}],
    }
    issues = validate_resource(patient_bad_literals, tx="off")
    assert any("Structural[identifier.0.use]" in i for i in issues)
    assert any("Structural[name.0.use]" in i for i in issues)
    assert any("Structural[telecom.0.system]" in i for i in issues)
    assert any("Structural[address.0.use]" in i for i in issues)


def test_servicerequest_requisition_type_extensible_binding() -> None:
    def _make_sr(coding: dict[str, str]) -> dict[str, Any]:
        return {
            "resourceType": "ServiceRequest",
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/1"},
            "requisition": {
                "type": {"coding": [coding]},
                "value": "REQ-1",
            },
        }

    valid_sr = _make_sr({"system": "http://terminology.hl7.org/CodeSystem/v2-0203", "code": "MR"})
    valid_warnings: list[str] = []
    assert validate_resource(valid_sr, _warnings_out=valid_warnings) == []
    assert valid_warnings == []

    invalid_sr = _make_sr({"system": "http://example.org/custom-system", "code": "NOT_A_TYPE"})
    warnings: list[str] = []
    issues = validate_resource(invalid_sr, _warnings_out=warnings)
    assert issues == []
    assert any("ServiceRequest.requisition.type" in w for w in warnings)

    strict_issues = validate_resource(invalid_sr, strict_extensible=True)
    assert any("ServiceRequest.requisition.type" in i for i in strict_issues)


def test_meta_security_binding() -> None:
    def _make_patient(system: str, sec_code: str) -> dict[str, Any]:
        return {
            "resourceType": "Patient",
            "meta": {
                "security": [
                    {
                        "system": system,
                        "code": sec_code,
                    }
                ]
            },
        }

    valid_warnings: list[str] = []
    assert (
        validate_resource(
            _make_patient("http://terminology.hl7.org/CodeSystem/v3-Confidentiality", "N"),
            _warnings_out=valid_warnings,
        )
        == []
    )
    assert valid_warnings == []

    warnings: list[str] = []
    assert (
        validate_resource(
            _make_patient("http://example.org/custom-security", "BOGUS_SEC"),
            _warnings_out=warnings,
        )
        == []
    )
    assert any("Patient.meta.security" in w for w in warnings)

    strict_issues = validate_resource(
        _make_patient("http://example.org/custom-security", "BOGUS_SEC"),
        strict_extensible=True,
    )
    assert any("Patient.meta.security" in i for i in strict_issues)


def test_usage_context_code_binding() -> None:
    def _make_ad(system: str, ctx_code: str) -> dict[str, Any]:
        return {
            "resourceType": "ActivityDefinition",
            "status": "active",
            "useContext": [
                {
                    "code": {
                        "system": system,
                        "code": ctx_code,
                    },
                    "valueCodeableConcept": {"text": "Adult"},
                }
            ],
        }

    valid_warnings: list[str] = []
    assert (
        validate_resource(
            _make_ad("http://terminology.hl7.org/CodeSystem/usage-context-type", "age"),
            _warnings_out=valid_warnings,
        )
        == []
    )
    assert valid_warnings == []

    warnings: list[str] = []
    assert (
        validate_resource(
            _make_ad("http://example.org/custom-ctx", "bogus-ctx"),
            _warnings_out=warnings,
        )
        == []
    )
    assert any("ActivityDefinition.useContext.code" in w for w in warnings)

    strict_issues = validate_resource(
        _make_ad("http://example.org/custom-ctx", "bogus-ctx"),
        strict_extensible=True,
    )
    assert any("ActivityDefinition.useContext.code" in i for i in strict_issues)


def test_expression_language_binding() -> None:
    def _make_rg(lang: str) -> dict[str, Any]:
        return {
            "resourceType": "RequestGroup",
            "status": "active",
            "intent": "order",
            "action": [
                {
                    "condition": [
                        {
                            "kind": "applicability",
                            "expression": {"language": lang, "expression": "true"},
                        }
                    ]
                }
            ],
        }

    valid_warnings: list[str] = []
    assert validate_resource(_make_rg("text/fhirpath"), _warnings_out=valid_warnings) == []
    assert valid_warnings == []

    warnings: list[str] = []
    assert validate_resource(_make_rg("text/bogus-lang"), _warnings_out=warnings) == []
    assert any("RequestGroup.action.condition.expression.language" in w for w in warnings)

    strict_issues = validate_resource(_make_rg("text/bogus-lang"), strict_extensible=True)
    assert any("RequestGroup.action.condition.expression.language" in i for i in strict_issues)


def test_reference_type_binding() -> None:
    def _make_patient(ref_type: str) -> dict[str, Any]:
        return {
            "resourceType": "Patient",
            "generalPractitioner": [
                {"reference": "Organization/1", "type": ref_type},
            ],
        }

    valid_warnings: list[str] = []
    assert validate_resource(_make_patient("Organization"), _warnings_out=valid_warnings) == []
    assert valid_warnings == []

    warnings: list[str] = []
    assert validate_resource(_make_patient("NotAResourceType"), _warnings_out=warnings) == []
    assert any("Patient.generalPractitioner.type" in w for w in warnings)

    strict_issues = validate_resource(_make_patient("NotAResourceType"), strict_extensible=True)
    assert any("Patient.generalPractitioner.type" in i for i in strict_issues)


def test_money_currency_required_binding() -> None:
    def _make_charge(currency: str) -> dict[str, Any]:
        return {
            "resourceType": "ChargeItem",
            "status": "billable",
            "code": {"text": "Consult"},
            "subject": {"reference": "Patient/1"},
            "priceOverride": {"value": 100.0, "currency": currency},
        }

    assert validate_resource(_make_charge("USD")) == []
    issues = validate_resource(_make_charge("NOT_A_CURRENCY"))
    assert any("ChargeItem.priceOverride.currency" in i for i in issues)


def test_attachment_content_type_required_binding() -> None:
    def _make_patient(mime: str) -> dict[str, Any]:
        return {
            "resourceType": "Patient",
            "photo": [{"contentType": mime, "data": "AQID"}],
        }

    assert validate_resource(_make_patient("image/png")) == []
    issues = validate_resource(_make_patient("not-a-mime-type"))
    assert any("Patient.photo.contentType" in i for i in issues)


def test_ig_profile_skip_paths_override() -> None:
    prof_url = "http://example.org/fhir/StructureDefinition/custom-sr"
    custom_vs_spec: dict[str, Any] = {
        "codes": ["CUSTOM_OK"],
        "system_codes": {"http://example.org/custom-system": ["CUSTOM_OK"]},
        "external_systems": [],
    }
    custom_profile = CompiledProfile(
        base_type="ServiceRequest",
        required=(),
        forbidden=(),
        max_one=(),
        fixed=(),
        pattern=(),
        type_narrowing=(),
        target_types=(),
        bindings=(),
        slices=(),
        binding_specs=(
            CompiledBindingRule(
                path="ServiceRequest.requisition.type",
                parts=("requisition", "type"),
                strength="required",
                value_set="http://example.org/fhir/ValueSet/custom-id-type",
                vs_spec=custom_vs_spec,
            ),
        ),
    )

    def _make_sr(code: str) -> dict[str, Any]:
        return {
            "resourceType": "ServiceRequest",
            "meta": {"profile": [prof_url]},
            "status": "active",
            "intent": "order",
            "subject": {"reference": "Patient/1"},
            "requisition": {
                "type": {
                    "coding": [
                        {
                            "system": "http://example.org/custom-system",
                            "code": code,
                        }
                    ]
                },
                "value": "REQ-1",
            },
        }

    # CUSTOM_OK is not in base identifier-type ValueSet, but IG profile overrides it.
    assert (
        validate_resource(
            _make_sr("CUSTOM_OK"),
            ig_sources={prof_url: custom_profile},
            strict_extensible=True,
        )
        == []
    )

    # Invalid code is reported once by the IG profile (not duplicated by COMPLEX_TYPE_BINDINGS).
    issues = validate_resource(
        _make_sr("CUSTOM_BAD"),
        ig_sources={prof_url: custom_profile},
        strict_extensible=True,
    )
    matching = [i for i in issues if "ServiceRequest.requisition.type" in i]
    assert len(matching) == 1
    assert matching[0].startswith(f"Profile[{prof_url}]: ")


def test_contained_resource_boundary_isolation_and_tx_off() -> None:
    sr: dict[str, Any] = {
        "resourceType": "ServiceRequest",
        "status": "active",
        "intent": "order",
        "subject": {"reference": "#pat1"},
        "contained": [
            {
                "resourceType": "Patient",
                "id": "pat1",
                "photo": [{"contentType": "not-a-mime-type", "data": "AQID"}],
            }
        ],
    }
    issues = validate_resource(sr)
    assert len(issues) == 1
    assert issues[0].startswith("contained[0]: ")
    assert "Patient.photo.contentType" in issues[0]
    assert not any("ServiceRequest.contained" in i for i in issues)

    # tx="off" skips complex datatype binding validation
    assert validate_resource(sr, tx="off") == []
