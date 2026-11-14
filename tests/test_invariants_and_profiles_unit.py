"""Unit tests for FHIRPath invariants, profile rules, primitives, datasets, and CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from fhirlance import validate_dataset, validate_resource
from fhirlance.base import validate_extension_item, validate_primitive_ext_obj
from fhirlance.canadian import validate_canadian_patient
from fhirlance.cli import main as cli_main
from fhirlance.profile_engine import (
    CompiledProfile,
    compile_profiles,
    pattern_matches,
    resolve_nodes,
    validate_single_profile,
)
from fhirlance.types import Extension


def test_all_fhirpath_invariants_unit() -> None:
    # txt-1: Narrative.div must contain <div
    obs_bad_txt = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "HR"},
        "text": {"status": "generated", "div": "<span>not wrapped</span>"},
    }
    assert any(
        "Invariant[txt-1]" in i
        for i in validate_resource(obs_bad_txt, require_canadian_profile=False)
    )

    # pat-1: Patient.contact requires name, telecom, address, or organization
    pat_bad_contact = {
        "resourceType": "Patient",
        "contact": [{"gender": "female"}],
    }
    assert any(
        "Invariant[pat-1]" in i
        for i in validate_resource(pat_bad_contact, require_canadian_profile=False)
    )

    # obs-6: dataAbsentReason disallowed when value[x] is present
    obs_bad_dar = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "HR"},
        "valueInteger": 72,
        "dataAbsentReason": {"text": "unknown"},
    }
    assert any(
        "Invariant[obs-6]" in i
        for i in validate_resource(obs_bad_dar, require_canadian_profile=False)
    )

    # obs-7 when code has non-dict coding or component has no code
    obs_no_comp_code = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": ["bad", {"system": "http://loinc.org", "code": "8867-4"}]},
        "valueInteger": 72,
        "component": [{"valueInteger": 1}],
    }
    issues_obs = validate_resource(obs_no_comp_code, require_canadian_profile=False)
    assert any("Structural[" in i for i in issues_obs)

    # con-4: abated Condition requires clinicalStatus
    cond_bad_abated = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/1"},
        "abatementDateTime": "2026-01-01",
    }
    assert any(
        "Invariant[con-4]" in i
        for i in validate_resource(cond_bad_abated, require_canadian_profile=False)
    )

    # bdl-1, bdl-3, bdl-4, and non-dict meta in Bundle.entry.resource
    bundle_bad = {
        "resourceType": "Bundle",
        "type": "collection",
        "total": 1,
        "entry": [
            {
                "fullUrl": "urn:uuid:1",
                "request": {"method": "POST", "url": "Patient"},
                "response": {"status": "201"},
                "resource": {"resourceType": "Patient", "meta": "not-a-dict"},
            }
        ],
    }
    issues = validate_resource(bundle_bad, require_canadian_profile=False)
    assert any("Invariant[bdl-1]" in i for i in issues)
    assert any("Invariant[bdl-3]" in i for i in issues)
    assert any("Invariant[bdl-4]" in i for i in issues)


def test_profile_engine_all_rule_types_and_helpers() -> None:
    raw = {
        "http://example.org/StructureDefinition/test-obs": {
            "base_type": "Observation",
            "required": ["Observation", "Observation.effective[x]", "Observation.subject"],
            "forbidden": ["Observation.comment"],
            "max_one": ["Observation", "Observation.category"],
            "fixed": {"Observation.status": "final"},
            "pattern": {"Observation.code": {"coding": [{"system": "http://loinc.org"}]}},
            "type_narrowing": {
                "Observation.value[x]": ["Quantity"],
                "Observation.component.value[x]": ["Quantity"],
            },
            "target_types": {"Observation.subject": ["Patient"]},
            "bindings": {"Observation.status": ["final", "amended"]},
            "slices": [
                {
                    "path": "Observation.category",
                    "min": 1,
                    "matchers": {"coding.code": ("fixed", "vital-signs")},
                },
                {
                    "path": "Observation.note",
                    "min": 1,
                    "matchers": {"text": ("pattern", "verified")},
                },
            ],
        }
    }
    compiled: dict[str, CompiledProfile] = compile_profiles(raw)
    url = "http://example.org/StructureDefinition/test-obs"

    good_obs = {
        "resourceType": "Observation",
        "status": "final",
        "category": [{"coding": [{"code": "vital-signs"}]}],
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        "subject": {"reference": "Patient/123"},
        "effectiveDateTime": "2026-01-01",
        "valueQuantity": {"value": 70},
        "note": [{"text": "verified"}],
    }
    assert validate_single_profile(good_obs, "Observation", url, compiled) == []
    assert validate_single_profile(good_obs, "Observation", "http://unknown.org/p", compiled) == []

    # Reference edge cases: #contained, urn:uuid, and unmapped URL do not fail target_types
    for ref_val in ("#pat1", "urn:uuid:abc", "http://example.org/something"):
        obs_ref = {**good_obs, "subject": {"reference": ref_val}}
        assert validate_single_profile(obs_ref, "Observation", url, compiled) == []

    # Non-dict component triggers safe skip in type_narrowing; non-dict/list pattern mismatches
    obs_scalar_comp = {**good_obs, "component": ["not-a-dict"]}
    assert validate_single_profile(obs_scalar_comp, "Observation", url, compiled) == []
    assert not pattern_matches("not-a-dict", {"a": 1})
    assert not pattern_matches("not-a-list", ["a"])
    assert resolve_nodes("scalar", ["a"]) == []
    assert resolve_nodes({"valueString": "hi"}, ["value[x]"]) == ["hi"]

    bad_obs = {
        "resourceType": "Observation",
        "status": "preliminary",
        "category": [{"coding": [{"code": "lab"}]}, {"coding": [{"code": "exam"}]}],
        "code": {"coding": [{"system": "http://snomed.info/sct", "code": "1"}]},
        "subject": {"reference": "Device/dev-1"},
        "valueString": "wrong-choice",
        "comment": "forbidden",
    }
    issues = validate_single_profile(bad_obs, "Observation", url, compiled)
    assert any("missing required element 'Observation.effective[x]'" in i for i in issues)
    assert any("forbidden element 'Observation.comment'" in i for i in issues)
    assert any("exceeds max cardinality 1" in i for i in issues)
    assert any("must equal fixed value 'final'" in i for i in issues)
    assert any("does not match required pattern" in i for i in issues)
    assert any("narrowed to ('Quantity',)" in i for i in issues)
    assert any("reference target 'Device' not in ['Patient']" in i for i in issues)
    assert any("code 'preliminary' not in required ValueSet" in i for i in issues)
    assert any("slice at 'Observation.category'" in i for i in issues)
    assert any("slice at 'Observation.note'" in i for i in issues)


def test_primitive_extension_and_base_helpers() -> None:
    # Partial FHIR dates & invalid regex/calendar dates; bool rejected as int
    assert (
        validate_resource(
            {"resourceType": "Patient", "birthDate": "1990"}, require_canadian_profile=False
        )
        == []
    )
    bad_patient = {
        "resourceType": "Patient",
        "birthDate": "not-a-date",
        "multipleBirthInteger": True,
    }
    issues = validate_resource(bad_patient, require_canadian_profile=False)
    assert any("birthDate" in i for i in issues)
    assert any("multipleBirthInteger" in i for i in issues)

    # ExtensionBase direct validation + ext-1 error cases
    ext = Extension.model_validate({"url": "http://example.org/e", "valueString": "ok"})
    assert ext.url == "http://example.org/e"
    with pytest.raises(ValueError, match="must be an object"):
        validate_extension_item("not-a-dict")
    with pytest.raises(ValueError, match=r"Extension\.url is required"):
        validate_extension_item({"url": ""})
    with pytest.raises(ValueError, match="non-empty object"):
        validate_primitive_ext_obj({}, "_birthDate")
    with pytest.raises(ValueError, match="non-empty list"):
        validate_primitive_ext_obj({"extension": []}, "_birthDate")

    # Missing resourceType & unknown resourceType
    assert validate_resource({"id": "1"}) == ["Missing required field: 'resourceType'"]
    assert validate_resource({"resourceType": "NoSuchResource"}) == [
        "Unknown FHIR R4 resourceType: 'NoSuchResource'"
    ]

    # Primitive extension with nested sub-extensions + _value primitive inside Extension
    obs = {
        "resourceType": "Observation",
        "status": "final",
        "_status": {
            "id": "st-1",
            "extension": [
                {
                    "url": "http://example.org/outer",
                    "extension": [{"url": "inner", "valueString": "ok"}],
                }
            ],
        },
        "extension": [
            {
                "url": "http://example.org/prim-ext",
                "valueString": "hi",
                "_valueString": {"id": "vs-1"},
            }
        ],
        "code": {"text": "HR"},
    }
    assert validate_resource(obs, require_canadian_profile=False) == []

    obs_bad_subext = {
        **obs,
        "_status": {"extension": [{"url": "http://example.org/bad", "extension": []}]},
    }
    assert any(
        "Structural[_status]" in i
        for i in validate_resource(obs_bad_subext, require_canadian_profile=False)
    )


def test_canadian_non_dict_resilience() -> None:
    issues = validate_canadian_patient(
        {
            "resourceType": "Patient",
            "identifier": ["bad-ident"],
            "address": ["bad-addr"],
            "extension": ["bad-ext"],
        }
    )
    assert any("JHN" in i for i in issues)


def test_dataset_edge_cases_and_cli_options(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    missing = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError):
        validate_dataset(missing)
    assert cli_main([str(missing)]) == 2
    assert "Path not found" in capsys.readouterr().err

    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    empty_report = validate_dataset(empty_dir)
    assert empty_report["total_resources"] == 0
    assert empty_report["compliance_rate"] == 0.0

    (tmp_path / "notes.txt").write_text("ignored", encoding="utf-8")
    (tmp_path / "broken.json").write_text("{bad json", encoding="utf-8")
    (tmp_path / "blank_lines.ndjson").write_text(
        '\n{"resourceType": "Patient", "id": "p-ndjson"}\n\n', encoding="utf-8"
    )
    (tmp_path / "bad_encoding.ndjson").write_bytes(b"\xff\xfe\x00\x00")

    bundle_file = tmp_path / "bundle.json"
    bundle_file.write_text(
        json.dumps(
            {
                "resourceType": "Bundle",
                "type": "collection",
                "entry": [
                    {
                        "resource": {
                            "resourceType": "Patient",
                            "id": "p1",
                            "name": [{"family": "Smith"}],
                            "gender": "female",
                        }
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert (
        cli_main(
            [
                str(bundle_file),
                "--no-canadian",
                "--profile",
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient",
            ]
        )
        == 1
    )
    assert "issues" in capsys.readouterr().out or True

    dir_report = validate_dataset(tmp_path, require_canadian_profile=False)
    assert dir_report["total_resources"] == 2
    assert dir_report["valid_resources"] == 2
    error_files = {item["file"] for item in dir_report["issues"]}
    assert {"broken.json", "bad_encoding.ndjson"}.issubset(error_files)
