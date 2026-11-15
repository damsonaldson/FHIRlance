"""Tests for first-class FHIR Extension StructureDefinition validation."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from fhirlance import (
    EXTENSION_CONSTRAINTS,
    clear_ig_cache,
    load_compiled_ig_extensions,
    load_raw_ig_extensions,
    register_ig,
    validate_resource,
)
from fhirlance.extensions import COMPILED_EXTENSIONS

if TYPE_CHECKING:
    from pathlib import Path


def _patient(**extra: Any) -> dict[str, Any]:
    return {"resourceType": "Patient", "id": "p1", **extra}


def _observation(**extra: Any) -> dict[str, Any]:
    return {
        "resourceType": "Observation",
        "id": "o1",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "29463-7"}]},
        **extra,
    }


def _nutrition_order(**extra: Any) -> dict[str, Any]:
    return {
        "resourceType": "NutritionOrder",
        "id": "no1",
        "status": "active",
        "intent": "order",
        "patient": {"reference": "Patient/p1"},
        "dateTime": "2025-01-01",
        **extra,
    }


class TestBuiltinExtensionCompilation:
    def test_builtin_extensions_compiled(self) -> None:
        assert len(EXTENSION_CONSTRAINTS) >= 400
        assert len(COMPILED_EXTENSIONS) == len(EXTENSION_CONSTRAINTS)
        assert "http://hl7.org/fhir/StructureDefinition/data-absent-reason" in COMPILED_EXTENSIONS
        assert "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race" in COMPILED_EXTENSIONS
        assert "http://hl7.org/fhir/StructureDefinition/request-doNotPerform" in COMPILED_EXTENSIONS
        assert (
            COMPILED_EXTENSIONS[
                "http://hl7.org/fhir/StructureDefinition/request-doNotPerform"
            ].is_modifier
            is True
        )

    def test_extension_inheritance_resolved(self) -> None:
        ca_addr = COMPILED_EXTENSIONS[
            "http://fhir.infoway-inforoute.ca/ca-ext/StructureDefinition/address-noFixedAddress"
        ]
        assert "boolean" in ca_addr.node.value_types


class TestContextValidation:
    def test_element_context_on_primitive_passes(self) -> None:
        p = _patient(
            _birthDate={
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "unknown",
                    }
                ]
            }
        )
        assert validate_resource(p) == []

    def test_element_context_on_resource_root_fails(self) -> None:
        p = _patient(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                    "valueCode": "unknown",
                }
            ]
        )
        issues = validate_resource(p)
        assert any("not valid in context" in m for m in issues)

    def test_specific_path_context_patient_birthtime(self) -> None:
        valid = _patient(
            birthDate="1990-01-01",
            _birthDate={
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
                        "valueDateTime": "1990-01-01T12:00:00Z",
                    }
                ]
            },
        )
        assert validate_resource(valid) == []

        invalid = _patient(
            name=[
                {
                    "family": "Doe",
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
                            "valueDateTime": "1990-01-01T12:00:00Z",
                        }
                    ],
                }
            ]
        )
        issues = validate_resource(invalid)
        assert any("not valid in context" in m for m in issues)

    def test_complex_type_and_element_context(self) -> None:
        valid = _patient(
            address=[
                {
                    "line": ["123 Main St"],
                    "_line": [
                        {
                            "extension": [
                                {
                                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-ADXP-streetName",
                                    "valueString": "Main St",
                                }
                            ]
                        }
                    ],
                }
            ]
        )
        assert validate_resource(valid) == []

        invalid = _patient(
            name=[
                {
                    "given": ["Alice"],
                    "_given": [
                        {
                            "extension": [
                                {
                                    "url": "http://hl7.org/fhir/StructureDefinition/iso21090-ADXP-streetName",
                                    "valueString": "Main St",
                                }
                            ]
                        }
                    ],
                }
            ]
        )
        issues = validate_resource(invalid)
        assert any("not valid in context" in m for m in issues)

    def test_resource_context_pertains_to_goal(self) -> None:
        valid = _observation(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/resource-pertainsToGoal",
                    "valueReference": {"reference": "Goal/g1"},
                }
            ]
        )
        assert validate_resource(valid) == []

        bad_target = _observation(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/resource-pertainsToGoal",
                    "valueReference": {"reference": "Patient/p1"},
                }
            ]
        )
        issues = validate_resource(bad_target)
        assert any("Reference target 'Patient' not in ['Goal']" in m for m in issues)


class TestValueAndBindingConstraints:
    def test_data_absent_reason_binding_and_type(self) -> None:
        bad_code = _patient(
            _birthDate={
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "definitely-invalid-code",
                    }
                ]
            }
        )
        issues = validate_resource(bad_code)
        assert any("Terminology" in m or "definitely-invalid-code" in m for m in issues)

        wrong_type = _patient(
            _birthDate={
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueString": "unknown",
                    }
                ]
            }
        )
        issues = validate_resource(wrong_type)
        assert any("requires value[x] type in ['valueCode']" in m for m in issues)


class TestComplexSubExtensionSlices:
    def test_us_core_race_valid_and_invalid(self) -> None:
        valid_race = {
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "extension": [
                {
                    "url": "ombCategory",
                    "valueCoding": {
                        "system": "urn:oid:2.16.840.1.113883.6.238",
                        "code": "2106-3",
                        "display": "White",
                    },
                },
                {"url": "text", "valueString": "White"},
            ],
        }
        assert validate_resource(_patient(extension=[valid_race])) == []

        # Wrong context (Observation)
        obs_issues = validate_resource(_observation(extension=[valid_race]))
        assert any("not valid in context" in m for m in obs_issues)

        # Missing required 'text' sub-extension
        missing_text = {
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "extension": [
                {
                    "url": "ombCategory",
                    "valueCoding": {
                        "system": "urn:oid:2.16.840.1.113883.6.238",
                        "code": "2106-3",
                    },
                }
            ],
        }
        issues = validate_resource(_patient(extension=[missing_text]))
        assert any("sub-extension 'text' requires at least 1 item(s)" in m for m in issues)

        # Exceeds max=1 on 'text'
        dup_text = {
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "extension": [
                {"url": "text", "valueString": "White"},
                {"url": "text", "valueString": "Other"},
            ],
        }
        issues = validate_resource(_patient(extension=[dup_text]))
        assert any("sub-extension 'text' allows at most 1 item(s)" in m for m in issues)

        # value[x] forbidden on complex extension
        with_val = {
            "url": "http://hl7.org/fhir/us/core/StructureDefinition/us-core-race",
            "valueString": "White",
        }
        issues = validate_resource(_patient(extension=[with_val]))
        assert any("value[x] is forbidden" in m for m in issues)


class TestModifierExtensionRules:
    def test_unknown_modifier_extension_rejected(self) -> None:
        p = _patient(
            modifierExtension=[{"url": "http://example.org/unknown-modifier", "valueBoolean": True}]
        )
        issues = validate_resource(p)
        assert any("unknown modifierExtension" in m for m in issues)

    def test_unknown_modifier_extension_on_primitive_rejected(self) -> None:
        p = _patient(
            _birthDate={
                "modifierExtension": [
                    {"url": "http://example.org/unknown-modifier", "valueBoolean": True}
                ]
            }
        )
        issues = validate_resource(p)
        assert any("unknown modifierExtension" in m for m in issues)

    def test_non_modifier_in_modifier_slot_rejected(self) -> None:
        p = _patient(
            _birthDate={
                "modifierExtension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "unknown",
                    }
                ]
            }
        )
        issues = validate_resource(p)
        assert any("isModifier=false" in m for m in issues)

    def test_modifier_in_regular_extension_slot_rejected(self) -> None:
        no = _nutrition_order(
            extension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/request-doNotPerform",
                    "valueBoolean": True,
                }
            ]
        )
        issues = validate_resource(no)
        assert any("must appear in 'modifierExtension'" in m for m in issues)

    def test_valid_modifier_extension_passes(self) -> None:
        no = _nutrition_order(
            modifierExtension=[
                {
                    "url": "http://hl7.org/fhir/StructureDefinition/request-doNotPerform",
                    "valueBoolean": True,
                }
            ]
        )
        assert validate_resource(no) == []


class TestRuntimeIGExtensionLoading:
    def test_custom_ig_extension_with_closed_slicing_and_inheritance(self, tmp_path: Path) -> None:
        ext_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/custom-closed-ext",
            "type": "Extension",
            "kind": "complex-type",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
            "context": [{"type": "element", "expression": "Patient"}],
            "differential": {
                "element": [
                    {"id": "Extension", "path": "Extension", "isModifier": False},
                    {
                        "id": "Extension.extension",
                        "path": "Extension.extension",
                        "min": 1,
                        "slicing": {"rules": "closed"},
                    },
                    {
                        "id": "Extension.extension:flag",
                        "path": "Extension.extension",
                        "sliceName": "flag",
                        "min": 1,
                        "max": "1",
                    },
                    {
                        "id": "Extension.extension:flag.url",
                        "path": "Extension.extension.url",
                        "fixedUri": "flag",
                    },
                    {
                        "id": "Extension.extension:flag.value[x]",
                        "path": "Extension.extension.value[x]",
                        "min": 1,
                        "type": [{"code": "boolean"}],
                    },
                    {
                        "id": "Extension.url",
                        "path": "Extension.url",
                        "fixedUri": "http://example.org/fhir/StructureDefinition/custom-closed-ext",
                    },
                    {"id": "Extension.value[x]", "path": "Extension.value[x]", "max": "0"},
                ]
            },
        }
        ig_dir = tmp_path / "ext_ig"
        ig_dir.mkdir()
        (ig_dir / "StructureDefinition-custom-closed-ext.json").write_text(
            json.dumps(ext_sd), encoding="utf-8"
        )

        raw = load_raw_ig_extensions([ig_dir])
        assert "http://example.org/fhir/StructureDefinition/custom-closed-ext" in raw
        compiled = load_compiled_ig_extensions([ig_dir])
        assert "http://example.org/fhir/StructureDefinition/custom-closed-ext" in compiled

        valid_p = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/custom-closed-ext",
                    "extension": [{"url": "flag", "valueBoolean": True}],
                }
            ]
        )
        assert validate_resource(valid_p, ig_sources=[ig_dir]) == []

        bad_slice_p = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/custom-closed-ext",
                    "extension": [
                        {"url": "flag", "valueBoolean": True},
                        {"url": "extra", "valueString": "nope"},
                    ],
                }
            ]
        )
        issues = validate_resource(bad_slice_p, ig_sources=[ig_dir])
        assert any("closed slice" in m for m in issues)

        # Register globally and clean up
        try:
            register_ig([ig_dir])
            assert validate_resource(valid_p) == []
        finally:
            clear_ig_cache()

    def test_extension_fixed_pattern_required_and_contexts(self, tmp_path: Path) -> None:
        base_ext = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/base-ext",
            "type": "Extension",
            "kind": "complex-type",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
            "context": [
                {"type": "element", "expression": "DomainResource"},
                {"type": "fhirpath", "expression": "Observation.value[x]"},
            ],
            "differential": {
                "element": [
                    {"id": "Extension", "path": "Extension", "isModifier": False},
                    {"id": "Extension.extension", "path": "Extension.extension", "max": "0"},
                    {
                        "id": "Extension.value[x]",
                        "path": "Extension.value[x]",
                        "min": 1,
                        "patternCodeableConcept": {
                            "coding": [{"system": "http://example.org/sys"}]
                        },
                    },
                ]
            },
        }
        derived_ext = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/derived-ext",
            "type": "Extension",
            "kind": "complex-type",
            "derivation": "constraint",
            "baseDefinition": "http://example.org/fhir/StructureDefinition/base-ext",
            "differential": {
                "element": [
                    {"id": "Extension", "path": "Extension"},
                    {
                        "id": "Extension.valueString",
                        "path": "Extension.valueString",
                        "fixedString": "locked",
                    },
                ]
            },
        }
        nested_parent = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/nested-parent",
            "type": "Extension",
            "kind": "complex-type",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
            "context": [{"type": "element", "expression": "Patient"}],
            "differential": {
                "element": [
                    {"id": "Extension", "path": "Extension"},
                    {"id": "Extension.extension", "path": "Extension.extension", "min": 1},
                    {"id": "Extension.value[x]", "path": "Extension.value[x]", "max": "0"},
                ]
            },
        }
        nested_child = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/nested-child",
            "type": "Extension",
            "kind": "complex-type",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
            "context": [
                {
                    "type": "extension",
                    "expression": "http://example.org/fhir/StructureDefinition/nested-parent",
                },
                {"type": "fhirpath", "expression": "Patient.birthDate.exists()"},
            ],
            "differential": {
                "element": [
                    {"id": "Extension", "path": "Extension"},
                    {"id": "Extension.extension", "path": "Extension.extension", "max": "0"},
                    {
                        "id": "Extension.value[x]",
                        "path": "Extension.value[x]",
                        "min": 1,
                        "type": [{"code": "string"}],
                    },
                ]
            },
        }
        ig_dir = tmp_path / "ext_features_ig"
        ig_dir.mkdir()
        for name, obj in (
            ("base", base_ext),
            ("derived", derived_ext),
            ("parent", nested_parent),
            ("child", nested_child),
        ):
            (ig_dir / f"StructureDefinition-{name}.json").write_text(
                json.dumps(obj), encoding="utf-8"
            )

        # pattern mismatch on base-ext
        bad_pat = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/base-ext",
                    "valueCodeableConcept": {
                        "coding": [{"system": "http://other.org", "code": "x"}]
                    },
                }
            ]
        )
        assert any(
            "does not match pattern" in m for m in validate_resource(bad_pat, ig_sources=[ig_dir])
        )

        # missing required value[x] on base-ext
        missing_val = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/base-ext",
                    "extension": [{"url": "sub", "valueString": "a"}],
                }
            ]
        )
        issues_mv = validate_resource(missing_val, ig_sources=[ig_dir])
        assert any("value[x] is required" in m for m in issues_mv)
        assert any("sub-extensions are forbidden" in m for m in issues_mv)

        # fixedString mismatch on derived-ext
        bad_fixed = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/derived-ext",
                    "valueString": "wrong",
                }
            ]
        )
        assert any(
            "must equal fixed value" in m for m in validate_resource(bad_fixed, ig_sources=[ig_dir])
        )

        # nested parent + child extension context
        valid_nested = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/nested-parent",
                    "extension": [
                        {
                            "url": "http://example.org/fhir/StructureDefinition/nested-child",
                            "valueString": "ok",
                        }
                    ],
                }
            ]
        )
        assert validate_resource(valid_nested, ig_sources=[ig_dir]) == []

        # nested-parent missing required sub-extension
        missing_sub = _patient(
            extension=[
                {
                    "url": "http://example.org/fhir/StructureDefinition/nested-parent",
                    "valueString": "bad",
                }
            ]
        )
        assert any(
            "at least one sub-extension is required" in m
            for m in validate_resource(missing_sub, ig_sources=[ig_dir])
        )

        # tx="off" skips terminology binding check on extension value[x]
        bad_dar = _patient(
            _birthDate={
                "extension": [
                    {
                        "url": "http://hl7.org/fhir/StructureDefinition/data-absent-reason",
                        "valueCode": "definitely-invalid-code",
                    }
                ]
            }
        )
        assert validate_resource(bad_dar, tx="off") == []
