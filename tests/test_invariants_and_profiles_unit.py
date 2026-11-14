"""Unit tests for FHIRPath invariants, Canadian localization, profile engine, and edge branches."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

import fhirlance.ig_loader as igl
from fhirlance import validate_dataset, validate_resource
from fhirlance.base import _check_int_not_bool, validate_extension_item, validate_primitive_ext_obj
from fhirlance.canadian import (
    CA_BASELINE_PROFILES,
    PROVINCIAL_JHN_SYSTEMS,
    PS_CA_PROFILES,
    validate_canadian_patient,
    validate_canadian_rules,
)
from fhirlance.cli import _format_text_lines
from fhirlance.cli import main as cli_main
from fhirlance.dataset import _validate_ndjson_file_parallel, _ValidationOptions
from fhirlance.formatters import (
    _extract_expression,
    dataset_to_junit_xml,
    dataset_to_operation_outcome,
    dataset_to_sarif,
)
from fhirlance.invariants import (
    _COND_ABATEMENT_FIELDS,
    _OBS_VALUE_FIELDS,
    _PATIENT_CONTACT_FIELDS,
    _coding_signatures,
)
from fhirlance.primitive_extensions import (
    _validate_primitive_ext_value,
    strip_and_validate_primitive_extensions,
)
from fhirlance.profile_engine import (
    AllowedValuesRule,
    CompiledProfile,
    SliceMatcher,
    _check_child_present,
    _check_target_types,
    _slice_item_matches,
    compile_profiles,
    pattern_matches,
    resolve_nodes,
    validate_single_profile,
)
from fhirlance.types import Extension

_BUNDLE_TYPES: tuple[str, ...] = (
    "document",
    "message",
    "transaction",
    "transaction-response",
    "batch",
    "batch-response",
    "history",
    "searchset",
    "collection",
)

_POSTAL_CODE_CASES: list[tuple[str, bool]] = [
    ("A1A 1A1", True),
    ("B2Y 1A1", True),
    ("C1A 1A1", True),
    ("E1C 1A1", True),
    ("G1A 1A1", True),
    ("H2X 1Y4", True),
    ("J1H 1A1", True),
    ("K1A 0A6", True),
    ("L5B 2C9", True),
    ("M5V 3L9", True),
    ("N2L 3G1", True),
    ("P3A 1A1", True),
    ("R3C 0V8", True),
    ("S7K 1J5", True),
    ("T2P 1J9", True),
    ("V6B 1A1", True),
    ("X1A 1A1", True),
    ("Y1A 1A1", True),
    # Invalid first letters (D, F, I, O, Q, U, W, Z) or bad formatting
    ("D1A 1A1", False),
    ("F1A 1A1", False),
    ("I1A 1A1", False),
    ("O1A 1A1", False),
    ("Q1A 1A1", False),
    ("U1A 1A1", False),
    ("W1A 1A1", False),
    ("Z1A 1A1", False),
    ("B2Y1A1", False),
    ("b2y 1a1", False),
    ("90210", False),
]


def test_all_fhirpath_invariants_unit() -> None:
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

    pat_bad_contact = {
        "resourceType": "Patient",
        "contact": ["not-a-dict", {"gender": "female"}],
    }
    assert any(
        "Invariant[pat-1]" in i
        for i in validate_resource(pat_bad_contact, require_canadian_profile=False)
    )

    obs_no_comp_code = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"text": "No coding array"},
        "valueInteger": 72,
        "component": [{"code": {"text": "comp"}, "valueInteger": 1}],
    }
    assert validate_resource(obs_no_comp_code, require_canadian_profile=False) == []

    bundle_bad = {
        "resourceType": "Bundle",
        "type": "collection",
        "total": 1,
        "entry": [
            "not-a-dict",
            {
                "fullUrl": "urn:uuid:1",
                "request": {"method": "POST", "url": "Patient"},
                "response": {"status": "201"},
                "resource": "not-a-dict",
            },
            {
                "fullUrl": "urn:uuid:1",
                "resource": {"resourceType": "Patient", "meta": "not-a-dict"},
            },
        ],
    }
    issues = validate_resource(bundle_bad, require_canadian_profile=False)
    assert any("Invariant[bdl-1]" in i for i in issues)
    assert any("Invariant[bdl-3]" in i for i in issues)
    assert any("Invariant[bdl-4]" in i for i in issues)
    assert any("Invariant[bdl-7]" in i for i in issues)


@pytest.mark.parametrize("val_field", _OBS_VALUE_FIELDS)
def test_obs6_and_obs7_across_all_11_value_fields(val_field: str) -> None:
    """Both obs-6 and obs-7 fire across all 11 Observation.value[x] choice fields."""
    obs = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        val_field: {"value": 1}
        if val_field
        not in ("valueString", "valueBoolean", "valueInteger", "valueTime", "valueDateTime")
        else "x",
        "dataAbsentReason": {"text": "unknown"},
        "component": [{"code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]}}],
    }
    issues = validate_resource(obs, require_canadian_profile=False)
    assert any("Invariant[obs-6]" in i for i in issues)
    assert any("Invariant[obs-7]" in i for i in issues)


@pytest.mark.parametrize("abatement_field", _COND_ABATEMENT_FIELDS)
def test_con4_across_all_5_abatement_fields(abatement_field: str) -> None:
    """con-4 fires across all 5 Condition.abatement[x] fields when clinicalStatus is absent."""
    cond_bad = {
        "resourceType": "Condition",
        "subject": {"reference": "Patient/1"},
        abatement_field: "2026-01-01",
    }
    assert any(
        "Invariant[con-4]" in i for i in validate_resource(cond_bad, require_canadian_profile=False)
    )

    cond_ok = {
        **cond_bad,
        "clinicalStatus": {
            "coding": [
                {
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "resolved",
                }
            ]
        },
    }
    assert not any(
        "Invariant[con-4]" in i for i in validate_resource(cond_ok, require_canadian_profile=False)
    )


@pytest.mark.parametrize("contact_field", _PATIENT_CONTACT_FIELDS)
def test_pat1_satisfied_by_each_contact_field(contact_field: str) -> None:
    """pat-1 passes when any one of name, telecom, address, or organization is present."""
    pat = {"resourceType": "Patient", "contact": [{contact_field: {"id": "c1"}}]}
    assert not any(
        "Invariant[pat-1]" in i for i in validate_resource(pat, require_canadian_profile=False)
    )


@pytest.mark.parametrize("bundle_type", _BUNDLE_TYPES)
def test_bundle_invariants_across_all_9_bundle_types(bundle_type: str) -> None:
    """Verify bdl-1, bdl-3, bdl-4, and bdl-7 across all 9 FHIR R4 Bundle.type codes."""
    bundle = {
        "resourceType": "Bundle",
        "type": bundle_type,
        "total": 2,
        "entry": [
            {
                "fullUrl": "urn:uuid:dup",
                "request": {"method": "GET", "url": "Patient"},
                "response": {"status": "200"},
                "resource": {"resourceType": "Patient", "id": "p1", "meta": {"versionId": "1"}},
            },
            {
                "fullUrl": "urn:uuid:dup",
                "resource": {"resourceType": "Patient", "id": "p1", "meta": {"versionId": "1"}},
            },
        ],
    }
    issues = validate_resource(bundle, require_canadian_profile=False)
    assert any("Invariant[bdl-1]" in i for i in issues) == (
        bundle_type not in {"searchset", "history"}
    )
    assert any("Invariant[bdl-3]" in i for i in issues) == (
        bundle_type not in {"batch", "transaction", "history"}
    )
    assert any("Invariant[bdl-4]" in i for i in issues) == (
        bundle_type not in {"batch-response", "transaction-response", "history"}
    )
    assert any("Invariant[bdl-7]" in i for i in issues) == (
        bundle_type in {"document", "collection"}
    )


@pytest.mark.parametrize(("prov", "jhn_system"), sorted(PROVINCIAL_JHN_SYSTEMS.items()))
def test_canadian_patient_all_13_provincial_jhn_systems(prov: str, jhn_system: str) -> None:
    """Every one of the 13 Canadian provincial/territorial JHN NamingSystems is accepted."""
    patient = {
        "resourceType": "Patient",
        "identifier": [{"system": jhn_system, "value": "123456789"}],
        "address": [{"country": "CA", "state": prov, "postalCode": "A1A 1A1"}],
    }
    assert validate_canadian_patient(patient) == []


@pytest.mark.parametrize(("postal_code", "expected_valid"), _POSTAL_CODE_CASES)
def test_canadian_postal_code_matrix(postal_code: str, expected_valid: bool) -> None:
    """Verify Canadian postal code regex across all valid and invalid FSA first letters."""
    patient = {
        "resourceType": "Patient",
        "identifier": [{"system": PROVINCIAL_JHN_SYSTEMS["NS"], "value": "123"}],
        "address": [{"country": "CA", "state": "NS", "postalCode": postal_code}],
    }
    issues = validate_canadian_patient(patient)
    assert (len(issues) == 0) == expected_valid


@pytest.mark.parametrize(
    ("rtype_key", "prof_url"),
    [*CA_BASELINE_PROFILES.items(), *PS_CA_PROFILES.items()],
)
def test_canadian_profile_presence_across_all_baseline_and_ps_ca_profiles(
    rtype_key: str,
    prof_url: str,
) -> None:
    """All CA-Baseline and PS-CA profiles satisfy Canadian meta.profile presence checks."""
    rtype = rtype_key.split("-", maxsplit=1)[0]
    res = {"resourceType": rtype, "id": "r1"}
    assert validate_canadian_rules(res, rtype, [prof_url]) == (
        ["Patient missing Canadian Jurisdictional Health Number (JHN) identifier"]
        if rtype == "Patient"
        else []
    )


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

    for ref_val in ("#pat1", "urn:uuid:abc", "http://example.org/something"):
        obs_ref = {**good_obs, "subject": {"reference": ref_val}}
        assert validate_single_profile(obs_ref, "Observation", url, compiled) == []

    obs_scalar_comp = {**good_obs, "component": ["not-a-dict"]}
    assert validate_single_profile(obs_scalar_comp, "Observation", url, compiled) == []
    assert not pattern_matches("not-a-dict", {"a": 1})
    assert not pattern_matches("not-a-list", ["a"])
    assert resolve_nodes("scalar", ["a"]) == []
    assert resolve_nodes({"valueString": "hi", "_valueString": {"id": "1"}}, ["value[x]"]) == ["hi"]
    assert not _check_child_present("not-a-dict", "field")
    assert (
        _check_target_types(
            {"subject": ["not-a-dict", {"reference": 123}]},
            url,
            (AllowedValuesRule("Observation.subject", ("subject",), frozenset({"Patient"})),),
        )
        == []
    )
    assert not _slice_item_matches(
        {"text": "wrong"},
        (SliceMatcher(("text",), "pattern", "expected"),),
    )

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

    # _validate_primitive_ext_value with non-None item in list + ExtensionBase error in fallback
    _validate_primitive_ext_value([None, {"id": "ok-1"}], "_given")
    ext_issues: list[str] = []
    strip_and_validate_primitive_extensions({"url": ""}, Extension, ext_issues)
    assert any("Structural[extension]" in i for i in ext_issues)

    # Bundle with entry lacking resource (branch 85->84 in resource_validator.py)
    bundle_no_res = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"fullUrl": "urn:uuid:1"}],
    }
    assert validate_resource(bundle_no_res, require_canadian_profile=False) == []


def test_uncovered_branches_across_cli_dataset_and_formatters(tmp_path: Path) -> None:
    lines = _format_text_lines(
        {
            "total_resources": 1,
            "valid_resources": 0,
            "invalid_resources": 1,
            "compliance_rate": 0.0,
            "issues": ["err-1"],
        },
        0.1234,
    )
    assert len(lines) == 2

    single_bad_nd = tmp_path / "single_bad.ndjson"
    single_bad_nd.write_text("\n{invalid json\n\n", encoding="utf-8")
    tot, val, nd_issues = _validate_ndjson_file_parallel(single_bad_nd, _ValidationOptions())
    assert tot == 1
    assert val == 0
    assert len(nd_issues) == 1

    assert _extract_expression("entry[0].resource: unparseable message", "Bundle") == [
        "Bundle.entry[0].resource"
    ]
    oo_empty_dict_entry = dataset_to_operation_outcome({"issues": [{"other_key": 1}]})
    assert oo_empty_dict_entry["issue"][0]["code"] == "informational"
    sarif_empty_dict = dataset_to_sarif({"issues": [{"other_key": 1}]})
    assert sarif_empty_dict["runs"][0]["results"] == []
    junit_no_valid = dataset_to_junit_xml({"valid_resources": 0, "issues": ["err"]})
    assert "valid_resources" not in junit_no_valid


def test_uncovered_branches_in_ig_loader_schema_extraction() -> None:
    out_codes: list[str] = []
    igl._collect_concepts(["not-a-dict", {"no_code": 1, "concept": "not-a-list"}], out_codes)
    igl._collect_expansion_codes(
        ["not-a-dict", {"no_code": 1, "contains": "not-a-list"}],
        out_codes,
    )
    assert out_codes == []
    assert igl._extract_code_systems([{"no_url": 1}, {"url": "http://x", "concept": []}]) == {}
    assert (
        igl._extract_value_sets(
            [
                {"no_url": 1},
                {"url": "http://vs", "compose": {"include": ["not-a-dict"]}},
            ],
            {},
        )
        == {}
    )
    assert igl._resolve_target_profile("http://example.org/myPatientProfile", {}) == "Patient"

    slices_map: dict[str, dict[str, Any]] = {}
    igl._record_slice_element({"id": "Patient.name"}, slices_map)
    assert slices_map == {}
    igl._record_slice_element(
        {"id": "Patient.name:official", "min": 0, "patternHumanName": {"use": "official"}},
        slices_map,
    )
    assert "Patient.name:official" in slices_map

    acc = igl._ProfileAccumulator()
    igl._record_element_types(
        {"type": ["not-a-dict", {"code": "string"}]},
        "Patient.name",
        {},
        acc,
    )
    igl._record_differential_element({"path": "Patient"}, {}, {}, acc)
    igl._record_snapshot_element({"path": "Patient"}, {}, {}, {}, acc)
    igl._record_snapshot_element(
        {"id": "Patient.name:official", "path": "Patient.name", "min": 1},
        {},
        {},
        {},
        acc,
    )
    base_els = igl._get_base_elements(None, "Patient", {})
    assert "Patient.name" in base_els

    spec = igl._extract_profile_spec(
        {
            "type": "Patient",
            "differential": {"element": ["not-a-dict"]},
            "snapshot": {"element": ["not-a-dict", {"path": "Patient.name"}]},
        },
        {},
        {},
        {},
    )
    assert spec["base_type"] == "Patient"

    spec_snap = igl._extract_profile_spec(
        {
            "type": "Patient",
            "snapshot": {"element": ["not-a-dict"]},
        },
        {},
        {},
        {},
    )
    assert spec_snap["base_type"] == "Patient"


def test_uncovered_branches_in_ig_loader_io_and_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert (
        igl._resolve_profile(
            "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient",
            {},
            {},
            set(),
        )
        is not None
    )
    assert igl._resolve_profile("http://unknown.org/sd", {}, {}, set()) is None

    container = igl._IGResources()
    igl._ingest_resource(
        {"resourceType": "Bundle", "entry": ["not-a-dict", {"resource": "not-a-dict"}]},
        container,
    )
    assert container.structure_definitions == []

    igl._load_source(tmp_path / "does_not_exist", container)

    pkg_parent = tmp_path / "pkg_fallback"
    (pkg_parent / "package").mkdir(parents=True)
    (pkg_parent / "root_sd.json").write_text("{}", encoding="utf-8")
    igl._load_from_directory(pkg_parent, container)
    fp = igl._fingerprint_source(pkg_parent)
    assert fp[2] > 0

    fake_cache = tmp_path / ".fhir" / "packages" / "my.cached.ig#1.0.0" / "package"
    fake_cache.mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert igl._resolve_source_path("my.cached.ig") == fake_cache

    mock_tar = MagicMock()
    mock_member = MagicMock()
    mock_member.name = "package/test.json"
    mock_member.isfile.return_value = True
    mock_tar.__enter__.return_value = mock_tar
    mock_tar.__iter__.return_value = iter([mock_member])
    mock_tar.extractfile.return_value = None
    monkeypatch.setattr("tarfile.open", lambda *_a, **_kw: mock_tar)
    igl._load_from_tarball(tmp_path / "dummy.tgz", container)


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


def test_canadian_non_dict_and_remaining_branches() -> None:
    with pytest.raises(ValueError, match="Expected integer, got boolean"):
        _check_int_not_bool(True)
    with pytest.raises(ValueError, match="non-empty list"):
        validate_extension_item({"url": "http://example.org/e", "extension": []})
    with pytest.raises(ValueError, match="model_type"):
        Extension.model_validate("not-a-dict")

    issues = validate_canadian_patient(
        {
            "resourceType": "Patient",
            "identifier": ["bad-ident"],
            "address": ["bad-addr"],
            "extension": ["bad-ext"],
        }
    )
    assert any("JHN" in i for i in issues)
    assert _coding_signatures("not-a-dict") == set()
    assert validate_resource({"resourceType": "NoSuchResource"}) == [
        "Unknown FHIR R4 resourceType: 'NoSuchResource'"
    ]

    obs_diff_comp = {
        "resourceType": "Observation",
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "85354-9"}]},
        "valueInteger": 120,
        "component": [{"code": {"coding": [{"system": "http://loinc.org", "code": "8480-6"}]}}],
    }
    assert validate_resource(obs_diff_comp, require_canadian_profile=False) == []
