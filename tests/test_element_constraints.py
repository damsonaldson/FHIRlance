"""Tests for Slice C: maxLength, min/maxValue, type.profile, empty lists, mustSupport."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fhirlance.cli import main as cli_main
from fhirlance.dataset import validate_dataset
from fhirlance.profile_engine import COMPILED_PROFILES, compile_profiles, validate_single_profile
from fhirlance.resource_validator import validate_resource


def _write_sd(directory: Path, name: str, sd: dict[str, Any]) -> Path:
    path = directory / f"{name}.json"
    path.write_text(json.dumps(sd), encoding="utf-8")
    return path


def _make_profile_sd(
    url: str,
    base_type: str,
    elements: list[dict[str, Any]],
    *,
    base_definition: str | None = None,
) -> dict[str, Any]:
    return {
        "resourceType": "StructureDefinition",
        "url": url,
        "name": url.rsplit("/", 1)[-1],
        "status": "active",
        "kind": "resource",
        "abstract": False,
        "type": base_type,
        "baseDefinition": base_definition or f"http://hl7.org/fhir/StructureDefinition/{base_type}",
        "derivation": "constraint",
        "differential": {"element": [{"id": base_type, "path": base_type}, *elements]},
    }


def _make_extension_sd(url: str, value_el: dict[str, Any]) -> dict[str, Any]:
    return {
        "resourceType": "StructureDefinition",
        "url": url,
        "name": url.rsplit("/", 1)[-1],
        "status": "active",
        "kind": "complex-type",
        "abstract": False,
        "type": "Extension",
        "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
        "derivation": "constraint",
        "context": [{"type": "element", "expression": "Patient"}],
        "differential": {
            "element": [
                {"id": "Extension", "path": "Extension"},
                {"id": "Extension.url", "path": "Extension.url", "fixedUri": url},
                {"id": "Extension.value[x]", "path": "Extension.value[x]", **value_el},
            ]
        },
    }


# ---------------------------------------------------------------------------
# maxLength
# ---------------------------------------------------------------------------


def test_max_length_compiled_profile() -> None:
    """Compiled profile enforces maxLength on string elements."""
    profiles = compile_profiles(
        {
            "http://example.org/sd/short-name": {
                "base_type": "Patient",
                "max_length": {"Patient.name.family": 5},
            }
        }
    )
    ok = {"resourceType": "Patient", "name": [{"family": "Smith"}]}
    assert (
        validate_single_profile(
            ok, "Patient", "http://example.org/sd/short-name", compiled_profiles=profiles
        )
        == []
    )

    bad = {"resourceType": "Patient", "name": [{"family": "TooLongFamily"}]}
    issues = validate_single_profile(
        bad, "Patient", "http://example.org/sd/short-name", compiled_profiles=profiles
    )
    assert any("maxLength 5" in i and "Patient.name.family" in i for i in issues)


def test_max_length_runtime_ig_and_inheritance(tmp_path: Path) -> None:
    """Runtime IG loader extracts maxLength and child profiles narrow via min()."""
    parent_url = "http://example.org/sd/parent-max-len"
    child_url = "http://example.org/sd/child-max-len"
    _write_sd(
        tmp_path,
        "parent",
        _make_profile_sd(
            parent_url,
            "Patient",
            [{"id": "Patient.name.family", "path": "Patient.name.family", "maxLength": 10}],
        ),
    )
    _write_sd(
        tmp_path,
        "child",
        _make_profile_sd(
            child_url,
            "Patient",
            [{"id": "Patient.name.family", "path": "Patient.name.family", "maxLength": 4}],
            base_definition=parent_url,
        ),
    )

    patient_ok = {"resourceType": "Patient", "name": [{"family": "John"}]}
    patient_mid = {"resourceType": "Patient", "name": [{"family": "Jonathan"}]}

    assert (
        validate_resource(patient_ok, profile_urls=[child_url], ig_sources=[tmp_path], tx="off")
        == []
    )
    issues = validate_resource(
        patient_mid, profile_urls=[child_url], ig_sources=[tmp_path], tx="off"
    )
    assert any("maxLength 4" in i for i in issues)


def test_max_length_extension_runtime_ig(tmp_path: Path) -> None:
    """Extension value_max_length is enforced for runtime-loaded extensions."""
    ext_url = "http://example.org/ext/short-code"
    _write_sd(
        tmp_path,
        "ext",
        _make_extension_sd(
            ext_url,
            {"type": [{"code": "string"}], "maxLength": 3},
        ),
    )
    ok = {
        "resourceType": "Patient",
        "extension": [{"url": ext_url, "valueString": "abc"}],
    }
    bad = {
        "resourceType": "Patient",
        "extension": [{"url": ext_url, "valueString": "abcd"}],
    }
    assert validate_resource(ok, ig_sources=[tmp_path], tx="off") == []
    issues = validate_resource(bad, ig_sources=[tmp_path], tx="off")
    assert any("maxLength 3" in i for i in issues)


# ---------------------------------------------------------------------------
# minValue[x] / maxValue[x]
# ---------------------------------------------------------------------------


def test_fhir_integer_32_bit_bounds() -> None:
    """FHIRInteger enforces 32-bit signed integer range [-2147483648, 2147483647]."""
    ok = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "x"},
        "valueInteger": 2147483647,
    }
    too_big = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "x"},
        "valueInteger": 2147483648,
    }
    too_small = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "x"},
        "valueInteger": -2147483649,
    }
    assert validate_resource(ok, tx="off") == []
    assert validate_resource(too_big, tx="off")
    assert validate_resource(too_small, tx="off")


def test_value_bounds_numeric_quantity_and_date_runtime_ig(tmp_path: Path) -> None:
    """minValue[x] and maxValue[x] enforce numeric, Quantity, and ISO date bounds."""
    prof_url = "http://example.org/sd/bounded-obs"
    _write_sd(
        tmp_path,
        "bounded",
        _make_profile_sd(
            prof_url,
            "Observation",
            [
                {
                    "id": "Observation.value[x]",
                    "path": "Observation.value[x]",
                    "minValueInteger": 0,
                    "maxValueInteger": 100,
                },
                {
                    "id": "Observation.referenceRange.low",
                    "path": "Observation.referenceRange.low",
                    "minValueQuantity": {"value": 10.0, "unit": "mg"},
                    "maxValueQuantity": {"value": 50.0, "unit": "mg"},
                },
                {
                    "id": "Observation.effectiveDateTime",
                    "path": "Observation.effectiveDateTime",
                    "minValueDateTime": "2020-01-01",
                    "maxValueDateTime": "2030-12-31",
                },
            ],
        ),
    )

    valid_obs = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "test"},
        "effectiveDateTime": "2024-06-01",
        "valueInteger": 50,
        "referenceRange": [{"low": {"value": 25.0, "unit": "mg"}}],
    }
    assert (
        validate_resource(valid_obs, profile_urls=[prof_url], ig_sources=[tmp_path], tx="off") == []
    )

    bad_obs = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "test"},
        "effectiveDateTime": "2019-12-31",
        "valueInteger": 150,
        "referenceRange": [{"low": {"value": 5.0, "unit": "mg"}}],
    }
    issues = validate_resource(bad_obs, profile_urls=[prof_url], ig_sources=[tmp_path], tx="off")
    assert any("Observation.value[x]" in i and "<= 100" in i for i in issues)
    assert any("Observation.referenceRange.low" in i and ">=" in i for i in issues)
    assert any("Observation.effectiveDateTime" in i and ">=" in i for i in issues)


def test_value_bounds_ignores_bool_and_handles_extension(tmp_path: Path) -> None:
    """Booleans are not treated as ints, and extensions enforce value_min/value_max."""
    ext_url = "http://example.org/ext/bounded-int"
    _write_sd(
        tmp_path,
        "ext",
        _make_extension_sd(
            ext_url,
            {"type": [{"code": "integer"}], "minValueInteger": 1, "maxValueInteger": 10},
        ),
    )
    ok = {"resourceType": "Patient", "extension": [{"url": ext_url, "valueInteger": 5}]}
    low = {"resourceType": "Patient", "extension": [{"url": ext_url, "valueInteger": 0}]}
    high = {"resourceType": "Patient", "extension": [{"url": ext_url, "valueInteger": 11}]}
    assert validate_resource(ok, ig_sources=[tmp_path], tx="off") == []
    assert any(">=" in i for i in validate_resource(low, ig_sources=[tmp_path], tx="off"))
    assert any("<=" in i for i in validate_resource(high, ig_sources=[tmp_path], tx="off"))

    profiles = compile_profiles(
        {
            "http://example.org/sd/bool-safe": {
                "base_type": "Observation",
                "min_values": {"Observation.value[x]": 1},
            }
        }
    )
    obs_bool = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "x"},
        "valueBoolean": False,
    }
    assert (
        validate_single_profile(
            obs_bool, "Observation", "http://example.org/sd/bool-safe", compiled_profiles=profiles
        )
        == []
    )


# ---------------------------------------------------------------------------
# type.profile (element_profiles)
# ---------------------------------------------------------------------------


def test_element_profile_simple_quantity_rejects_comparator() -> None:
    """Built-in cholesterol profile uses SimpleQuantity on high, rejecting comparator."""
    obs = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [{"system": "http://loinc.org", "code": "2093-3", "display": "Cholesterol"}]
        },
        "subject": {"reference": "Patient/1"},
        "effectiveDateTime": "2024-01-01",
        "valueQuantity": {
            "value": 180,
            "unit": "mg/dL",
            "system": "http://unitsofmeasure.org",
            "code": "mg/dL",
        },
        "referenceRange": [{"high": {"value": 200, "comparator": "<"}}],
    }
    issues = validate_single_profile(
        obs,
        "Observation",
        "http://hl7.org/fhir/StructureDefinition/cholesterol",
        compiled_profiles=COMPILED_PROFILES,
        tx="off",
    )
    assert any("Observation.referenceRange.high" in i and "SimpleQuantity" in i for i in issues)

    obs["referenceRange"] = [{"high": {"value": 200}}]
    issues_ok = validate_single_profile(
        obs,
        "Observation",
        "http://hl7.org/fhir/StructureDefinition/cholesterol",
        compiled_profiles=COMPILED_PROFILES,
        tx="off",
    )
    assert not any(
        "Observation.referenceRange.high" in i and "SimpleQuantity" in i for i in issues_ok
    )


def test_element_profile_codeable_concept_uv_ips() -> None:
    """CodeableConcept-uv-ips enforces Coding-uv-ips on CodeableConcept.coding."""
    profiles = compile_profiles(
        {
            "http://example.org/sd/cc-ips-user": {
                "base_type": "Condition",
                "element_profiles": {
                    "Condition.code": [
                        "http://hl7.org/fhir/uv/ips/StructureDefinition/CodeableConcept-uv-ips"
                    ]
                },
            }
        }
    )
    merged = {**COMPILED_PROFILES, **profiles}
    cond = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/1"},
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "123"}]},
    }
    assert (
        validate_single_profile(
            cond,
            "Condition",
            "http://example.org/sd/cc-ips-user",
            compiled_profiles=merged,
            tx="off",
        )
        == []
    )


def test_element_profile_custom_runtime_ig_with_choice_expansion(tmp_path: Path) -> None:
    """Runtime IG extracts type.profile including [x] choice expansion and validates against it."""
    simple_qty_url = "http://example.org/sd/custom-simple-qty"
    obs_prof_url = "http://example.org/sd/obs-simple-qty"
    _write_sd(
        tmp_path,
        "custom_sq",
        _make_profile_sd(
            simple_qty_url,
            "Quantity",
            [{"id": "Quantity.comparator", "path": "Quantity.comparator", "max": "0"}],
        ),
    )
    _write_sd(
        tmp_path,
        "obs_sq",
        _make_profile_sd(
            obs_prof_url,
            "Observation",
            [
                {
                    "id": "Observation.value[x]",
                    "path": "Observation.value[x]",
                    "type": [{"code": "Quantity", "profile": [f"{simple_qty_url}|1.0.0"]}],
                }
            ],
        ),
    )

    bad = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "test"},
        "valueQuantity": {"value": 5, "comparator": ">"},
    }
    issues = validate_resource(bad, profile_urls=[obs_prof_url], ig_sources=[tmp_path], tx="off")
    assert any("Observation.valueQuantity" in i and simple_qty_url in i for i in issues)

    ok = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "test"},
        "valueQuantity": {"value": 5},
    }
    assert validate_resource(ok, profile_urls=[obs_prof_url], ig_sources=[tmp_path], tx="off") == []


# ---------------------------------------------------------------------------
# Empty-list min >= 1 and max = 0 edge cases
# ---------------------------------------------------------------------------


def test_empty_list_required_and_forbidden_edge_cases() -> None:
    """Empty lists and all-None lists fail min>=1 checks and are caught by max=0."""
    profiles = compile_profiles(
        {
            "http://example.org/sd/req-name": {
                "base_type": "Patient",
                "required": ["Patient.name", "Patient.name.given"],
            },
            "http://example.org/sd/forb-name": {
                "base_type": "Patient",
                "forbidden": ["Patient.name"],
            },
        }
    )

    empty_name: dict[str, Any] = {"resourceType": "Patient", "name": []}
    issues_empty = validate_single_profile(
        empty_name, "Patient", "http://example.org/sd/req-name", compiled_profiles=profiles
    )
    assert any("Patient.name" in i for i in issues_empty)

    none_name: dict[str, Any] = {"resourceType": "Patient", "name": [None]}
    issues_none = validate_single_profile(
        none_name, "Patient", "http://example.org/sd/req-name", compiled_profiles=profiles
    )
    assert any("Patient.name" in i for i in issues_none)

    empty_given: dict[str, Any] = {"resourceType": "Patient", "name": [{"given": []}]}
    issues_given = validate_single_profile(
        empty_given, "Patient", "http://example.org/sd/req-name", compiled_profiles=profiles
    )
    assert any("Patient.name.given" in i for i in issues_given)

    issues_forb = validate_single_profile(
        empty_name, "Patient", "http://example.org/sd/forb-name", compiled_profiles=profiles
    )
    assert any("forbidden element 'Patient.name'" in i for i in issues_forb)


# ---------------------------------------------------------------------------
# --enforce-must-support
# ---------------------------------------------------------------------------


def test_must_support_off_by_default_and_on_everywhere(tmp_path: Path) -> None:
    """mustSupport is off by default; enforced via validate_resource, validate_dataset, and CLI."""
    ig_dir = tmp_path / "ig"
    ig_dir.mkdir()
    parent_url = "http://example.org/sd/ms-parent"
    child_url = "http://example.org/sd/ms-child"
    _write_sd(
        ig_dir,
        "parent",
        _make_profile_sd(
            parent_url,
            "Patient",
            [
                {"id": "Patient.birthDate", "path": "Patient.birthDate", "mustSupport": True},
                {"id": "Patient.gender", "path": "Patient.gender", "mustSupport": True},
            ],
        ),
    )
    _write_sd(
        ig_dir,
        "child",
        _make_profile_sd(
            child_url,
            "Patient",
            [
                {"id": "Patient.name", "path": "Patient.name", "mustSupport": True},
                # Forbidden elements must not be treated as mustSupport even if flagged
                {
                    "id": "Patient.gender",
                    "path": "Patient.gender",
                    "max": "0",
                    "mustSupport": True,
                },
            ],
            base_definition=parent_url,
        ),
    )

    # Missing inherited Patient.birthDate and child Patient.name; Patient.gender is forbidden.
    patient = {
        "resourceType": "Patient",
        "meta": {"profile": [child_url]},
        "id": "p1",
    }
    # 1) Off by default
    assert validate_resource(patient, ig_sources=[ig_dir], tx="off") == []

    # 2) On via validate_resource (inherited mustSupport + forbidden exclusion)
    issues = validate_resource(patient, ig_sources=[ig_dir], tx="off", enforce_must_support=True)
    assert any("Patient.birthDate" in i for i in issues)
    assert any("Patient.name" in i for i in issues)
    assert not any("Patient.gender" in i for i in issues)

    # 3) Nested resources: Bundle.entry and contained
    bundle_file = tmp_path / "bundle.json"
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "nested-1",
                    "meta": {"profile": [child_url]},
                    "link": [{"other": {"reference": "#contained-1"}, "type": "seealso"}],
                    "contained": [
                        {
                            "resourceType": "Patient",
                            "id": "contained-1",
                            "meta": {"profile": [child_url]},
                        }
                    ],
                }
            }
        ],
    }
    bundle_file.write_text(json.dumps(bundle), encoding="utf-8")

    report_off = validate_dataset(bundle_file, ig_sources=[ig_dir], tx="off")
    assert report_off["invalid_resources"] == 0

    report_on = validate_dataset(
        bundle_file, ig_sources=[ig_dir], tx="off", enforce_must_support=True
    )
    assert report_on["invalid_resources"] == 1
    flat_issues = [msg for entry in report_on["issues"] for msg in entry.get("issues", [])]
    assert any("Patient.birthDate" in msg for msg in flat_issues)
    assert any("contained[0]" in msg for msg in flat_issues)

    # 4) CLI --enforce-must-support
    exit_off = cli_main([str(bundle_file), "-ig", str(ig_dir), "-tx", "off"])
    assert exit_off == 0
    exit_on = cli_main(
        [str(bundle_file), "-ig", str(ig_dir), "-tx", "off", "--enforce-must-support"]
    )
    assert exit_on == 1
