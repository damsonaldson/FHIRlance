"""Comprehensive tests for output formatters, dynamic IG loading, and intra-file parallelism."""

from __future__ import annotations

import io
import json
import os
import runpy
import sys
import tarfile
from pathlib import Path
from typing import Any

import pytest
from defusedxml.ElementTree import fromstring as xml_fromstring  # type: ignore[import-untyped]

import fhirlance.ig_loader as igl
from fhirlance.cli import main as cli_main
from fhirlance.dataset import (
    _validate_file,
    _validate_file_parallel,
    _validate_json_file,
    _validate_json_file_parallel,
    _validate_ndjson_chunk,
    _validate_ndjson_file,
    _validate_ndjson_file_parallel,
    _validate_resource_batch,
    _ValidationOptions,
    validate_dataset,
)
from fhirlance.formatters import (
    SUPPORTED_OUTPUT_FORMATS,
    _classify_issue_code,
    _classify_sarif_rule_id,
    _extract_expression,
    _format_diagnostics,
    _infer_resource_type,
    _normalize_uri,
    _sanitize_xml,
    dataset_to_junit_xml,
    dataset_to_operation_outcome,
    dataset_to_sarif,
    format_dataset_report,
    issues_to_operation_outcome,
    validate_to_operation_outcome,
)
from fhirlance.ig_loader import (
    _find_cached_package,
    _fingerprint_source,
    _resolve_target_profile,
    clear_ig_cache,
    load_compiled_ig_profiles,
    load_raw_ig_profiles,
    register_ig,
)
from fhirlance.profile_engine import COMPILED_PROFILES
from fhirlance.resource_validator import validate_resource


def _valid_patient_dict() -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "pat-test-1",
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
        "name": [{"family": "Smith", "given": ["Alice"]}],
        "telecom": [{"system": "phone", "value": "902-555-0199"}],
        "gender": "female",
        "birthDate": "1995-04-12",
        "address": [{"city": "Halifax", "state": "NS", "postalCode": "B3H 1A1", "country": "CA"}],
    }


def _invalid_patient_dict() -> dict[str, Any]:
    return {
        "resourceType": "Patient",
        "id": "bad-pat",
        "gender": "unknown-invalid-gender",
    }


# ==============================================================================
# SECTION 1: Output Formatters & OperationOutcome Conformance
# ==============================================================================


class TestOutputFormatters:
    def test_issues_to_operation_outcome_empty(self) -> None:
        oo = issues_to_operation_outcome([])
        assert oo["resourceType"] == "OperationOutcome"
        assert len(oo["issue"]) == 1
        assert oo["issue"][0]["severity"] == "information"
        assert oo["issue"][0]["code"] == "informational"
        assert validate_resource(oo, require_canadian_profile=False) == []

    def test_issues_to_operation_outcome_classifications(self) -> None:
        issues = [
            "Structural[name.0]: field required",
            "Invariant[pat-1] Patient: gender must be lowercase",
            "not in required ValueSet http://example.org/vs: invalid code 'XYZ'",
            "missing required element 'identifier'",
            "Profile[http://example.org/p]: slice at 'component' requires at least 1 item",
            "Address[0] state US-only province is invalid",
            "Arbitrary error message",
        ]
        oo = issues_to_operation_outcome(issues, resource_type="Patient", resource_id="pat-1")
        assert oo["resourceType"] == "OperationOutcome"
        assert len(oo["issue"]) == len(issues)

        codes = [i["code"] for i in oo["issue"]]
        assert codes[0] == "structure"
        assert codes[1] == "invariant"
        assert codes[2] == "code-invalid"
        assert codes[3] == "required"
        assert codes[4] == "value"
        assert codes[5] == "value"
        assert codes[6] == "invalid"

        assert validate_resource(oo, require_canadian_profile=False) == []

    def test_nested_and_expression_extraction(self) -> None:
        assert _classify_issue_code("entry[0].resource: Structural[id]: error") == "structure"
        assert _classify_issue_code("contained[1]: ext-1 invariant error") == "invariant"
        assert _classify_issue_code("missing Canadian meta.profile") == "required"

        expr1 = _extract_expression("entry[0].resource: Structural[name.0]: missing", "Bundle")
        assert expr1 == ["Bundle.entry[0].resource.name[0]"]

        expr2 = _extract_expression("Profile[http://test]: 'Observation.code' missing", None)
        assert expr2 == ["Observation.code"]

        expr3 = _extract_expression("Address[0] postalCode invalid", "Patient")
        assert expr3 == ["Patient.address[0].postalCode"]

        expr4 = _extract_expression("Unparseable issue without path", "Patient")
        assert expr4 is None

    def test_infer_resource_type(self) -> None:
        assert _infer_resource_type({"resourceType": "Patient"}) == "Patient"
        assert _infer_resource_type({"resource_type": "Observation"}) == "Observation"
        assert _infer_resource_type({"issues": ["Resource Condition/c1: error"]}) == "Condition"
        assert _infer_resource_type({"issues": ["Encounter.status: error"]}) == "Encounter"
        assert _infer_resource_type({"file": "path/to/Patient.json"}) == "Patient"
        assert _infer_resource_type({"file": "random_file.ndjson"}) is None

    def test_dataset_to_operation_outcome_matrix(self) -> None:
        # Empty report
        empty_oo = dataset_to_operation_outcome({"issues": []})
        assert empty_oo["resourceType"] == "OperationOutcome"
        assert validate_resource(empty_oo, require_canadian_profile=False) == []

        # Non-dict and string items
        str_oo = dataset_to_operation_outcome({"issues": ["Raw string issue", 12345]})
        assert len(str_oo["issue"]) == 2
        assert validate_resource(str_oo, require_canadian_profile=False) == []

        # Parse error with line and without line
        report_with_parse_errors: dict[str, Any] = {
            "issues": [
                {"file": "bad.json", "error": "Invalid JSON syntax"},
                {"file": "bad.ndjson", "line": 5, "error": "Unterminated string"},
                {
                    "file": "valid_file.json",
                    "id": "p1",
                    "issues": ["Structural[telecom]: invalid"],
                },
            ]
        }
        oo = dataset_to_operation_outcome(report_with_parse_errors)
        assert len(oo["issue"]) == 3
        assert oo["issue"][0]["code"] == "exception"
        assert "bad.json: Invalid JSON syntax" in oo["issue"][0]["diagnostics"]
        assert "bad.ndjson:5: Unterminated string" in oo["issue"][1]["diagnostics"]
        assert validate_resource(oo, require_canadian_profile=False) == []

    def test_validate_to_operation_outcome_helper(self) -> None:
        valid_pat = _valid_patient_dict()
        oo_valid = validate_to_operation_outcome(valid_pat, require_canadian_profile=True)
        assert oo_valid["resourceType"] == "OperationOutcome"
        assert oo_valid["issue"][0]["code"] == "informational"
        assert validate_resource(oo_valid, require_canadian_profile=False) == []

        invalid_pat = _invalid_patient_dict()
        oo_invalid = validate_to_operation_outcome(invalid_pat, require_canadian_profile=False)
        assert oo_invalid["resourceType"] == "OperationOutcome"
        assert len(oo_invalid["issue"]) >= 1
        assert "Patient/bad-pat" in oo_invalid["issue"][0]["diagnostics"]
        assert validate_resource(oo_invalid, require_canadian_profile=False) == []

        oo_scalar = validate_to_operation_outcome("not a dict")
        assert len(oo_scalar["issue"]) == 1
        assert validate_resource(oo_scalar, require_canadian_profile=False) == []

    def test_sarif_formatter(self) -> None:
        assert _classify_sarif_rule_id("Invariant[ext-1]") == "FHIR002-Invariant"
        assert _classify_sarif_rule_id("no Canadian profile") == "FHIR004-Canadian"
        assert _classify_sarif_rule_id("Profile[http://x]") == "FHIR003-Profile"
        assert _classify_sarif_rule_id("Structural[name]") == "FHIR001-Structural"

        assert (
            _normalize_uri(r"C:\Code\FHIRlance\test.json") == "file:///C:/Code/FHIRlance/test.json"
        )
        assert _normalize_uri("relative/test.ndjson") == "relative/test.ndjson"

        report: dict[str, Any] = {
            "issues": [
                "Raw string issue",
                42,
                {"file": r"C:\data\bad.json", "error": "EOF reached"},
                {
                    "file": "dir/patient.json",
                    "line": 10,
                    "issues": [
                        "Structural[gender]: invalid",
                        "Invariant[pat-1]: gender rule",
                    ],
                },
            ]
        }
        sarif = dataset_to_sarif(report)
        assert sarif["version"] == "2.1.0"
        results = sarif["runs"][0]["results"]
        assert len(results) == 5

        # Verify ruleIndex is present and matches SARIF rules catalog
        for res in results:
            assert "ruleId" in res
            assert "ruleIndex" in res
            assert isinstance(res["ruleIndex"], int)
            assert res["message"]["text"] != ""

    def test_junit_xml_formatter(self) -> None:
        # Sanitization of control characters
        raw_bad = "Invalid\x00xml\x08char\x1fhere"
        clean = _sanitize_xml(raw_bad)
        assert clean == "Invalidxmlcharhere"

        report: dict[str, Any] = {
            "elapsed_seconds": None,  # Test null elapsed_seconds
            "valid_resources": 5,
            "issues": [
                {"file": "corrupt.json", "error": "Invalid\x00bytes"},
                {"file": "corrupt_line.ndjson", "line": 2, "error": "Syntax error"},
                {
                    "file": "patient.json",
                    "id": "p123",
                    "issues": ["Structural[telecom]: missing value"],
                },
                "Raw issue string in junit",
            ],
        }
        xml_str = dataset_to_junit_xml(report)
        assert xml_str.startswith('<?xml version="1.0" encoding="utf-8"?>')
        root = xml_fromstring(xml_str)
        assert root.attrib["time"] == "0.0000"
        assert root.attrib["failures"] == "4"

        # Test empty dataset
        empty_xml = dataset_to_junit_xml({"valid_resources": 0, "issues": []})
        root_empty = xml_fromstring(empty_xml)
        assert root_empty.attrib["failures"] == "0"

    def test_format_dataset_report_dispatcher(self) -> None:
        rep: dict[str, Any] = {
            "total_resources": 2,
            "valid_resources": 1,
            "invalid_resources": 1,
            "compliance_rate": 50.0,
            "issues": [{"file": "f.json", "issues": ["error"]}],
        }
        for fmt in SUPPORTED_OUTPUT_FORMATS:
            out = format_dataset_report(rep, fmt.upper())
            assert len(out) > 0

        with pytest.raises(ValueError, match="Unknown output format"):
            format_dataset_report(rep, "yaml")


# ==============================================================================
# SECTION 2: Dynamic IG Loading across all 4 source types
# ==============================================================================


class TestDynamicIGLoader:
    def test_target_profile_slug_resolution(self) -> None:
        sd_type_map = {"http://example.org/sd/custom": "CustomPatient"}
        # 1. in sd_type_by_url
        res1 = _resolve_target_profile("http://example.org/sd/custom|1.0", sd_type_map)
        assert res1 == "CustomPatient"
        # 2. in PROFILE_CONSTRAINTS
        assert (
            _resolve_target_profile(
                "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient",
                {},
            )
            == "Patient"
        )
        # 3. Slug in RESOURCE_MODELS
        assert (
            _resolve_target_profile("http://hl7.org/fhir/StructureDefinition/Patient", {})
            == "Patient"
        )
        # 4. Token/case-insensitive match (longest match first: MedicationRequest before Medication)
        assert (
            _resolve_target_profile(
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medicationrequest",
                {},
            )
            == "MedicationRequest"
        )
        assert (
            _resolve_target_profile(
                "http://hl7.org/fhir/us/core/StructureDefinition/us-core-medication",
                {},
            )
            == "Medication"
        )
        # 5. Unresolvable slug returns empty string
        assert _resolve_target_profile("http://example.org/completely-unknown-thing", {}) == ""

    def test_load_structure_definition_single_file(self, tmp_path: Path) -> None:
        sd_file = tmp_path / "custom-patient-sd.json"
        sd_file.write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/fhir/StructureDefinition/strict-patient",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient|4.0.1",
                    "differential": {
                        "element": [
                            {
                                "id": "Patient.active",
                                "path": "Patient.active",
                                "fixedBoolean": True,
                            },
                            {"id": "Patient.gender", "path": "Patient.gender", "max": "0"},
                            {
                                "id": "Patient.deceased[x]",
                                "path": "Patient.deceased[x]",
                                "max": "1",
                            },
                            {
                                "id": "Patient.generalPractitioner",
                                "path": "Patient.generalPractitioner",
                                "type": [
                                    {
                                        "code": "Reference",
                                        "targetProfile": [
                                            "http://example.org/StructureDefinition/profile-practitioner",
                                            "http://example.org/unknown-target",
                                        ],
                                    }
                                ],
                            },
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        clear_ig_cache()
        raw = load_raw_ig_profiles([sd_file])
        assert "http://example.org/fhir/StructureDefinition/strict-patient" in raw
        prof = raw["http://example.org/fhir/StructureDefinition/strict-patient"]
        assert prof["fixed"]["Patient.active"] is True
        assert "Patient.gender" in prof["forbidden"]
        assert "Patient.deceased[x]" in prof["max_one"]
        assert prof["target_types"]["Patient.generalPractitioner"] == ["Practitioner"]

        # Validate resource against this loaded profile
        test_patient = {
            "resourceType": "Patient",
            "active": True,
            "generalPractitioner": [{"reference": "Practitioner/dr-1"}],
        }
        issues = validate_resource(
            test_patient,
            require_canadian_profile=False,
            profile_urls=["http://example.org/fhir/StructureDefinition/strict-patient"],
            ig_sources=[sd_file],
        )
        assert issues == []

        bad_patient = {
            "resourceType": "Patient",
            "active": False,  # wrong fixed boolean
            "gender": "male",  # forbidden
            "generalPractitioner": [{"reference": "Device/dev-1"}],  # wrong target type
        }
        bad_issues = validate_resource(
            bad_patient,
            require_canadian_profile=False,
            profile_urls=["http://example.org/fhir/StructureDefinition/strict-patient"],
            ig_sources=[sd_file],
        )
        assert any("forbidden element 'Patient.gender'" in i for i in bad_issues)
        assert any("reference target 'Device' not in" in i for i in bad_issues)

    def test_load_bundle_with_sd_vs_cs_and_slices(self, tmp_path: Path) -> None:
        bundle_file = tmp_path / "ig_bundle.json"
        bundle_file.write_text(
            json.dumps(
                {
                    "resourceType": "Bundle",
                    "type": "collection",
                    "entry": [
                        {
                            "resource": {
                                "resourceType": "CodeSystem",
                                "url": "http://example.org/cs/custom-status",
                                "concept": [
                                    {
                                        "code": "active",
                                        "concept": [{"code": "active-trial"}],
                                    },
                                    {"code": "inactive"},
                                ],
                            }
                        },
                        {
                            "resource": {
                                "resourceType": "ValueSet",
                                "url": "http://example.org/vs/allowed-status",
                                "compose": {
                                    "include": [{"system": "http://example.org/cs/custom-status"}]
                                },
                            }
                        },
                        {
                            "resource": {
                                "resourceType": "StructureDefinition",
                                "url": "http://example.org/sd/status-observation",
                                "kind": "resource",
                                "type": "Observation",
                                "derivation": "constraint",
                                "differential": {
                                    "element": [
                                        {
                                            "id": "Observation.status",
                                            "path": "Observation.status",
                                            "binding": {
                                                "strength": "required",
                                                "valueSet": "http://example.org/vs/allowed-status|1.0",
                                            },
                                        },
                                        {
                                            "id": "Observation.component:systolic",
                                            "path": "Observation.component",
                                            "min": 1,
                                        },
                                        {
                                            "id": (
                                                "Observation.component:systolic"
                                                ".code.coding:SBPCode.code"
                                            ),
                                            "path": "Observation.component.code.coding.code",
                                            "fixedCode": "8480-6",
                                        },
                                    ]
                                },
                            }
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )

        clear_ig_cache()
        raw = load_raw_ig_profiles([bundle_file])
        spec = raw["http://example.org/sd/status-observation"]
        assert "Observation.status" in spec["bindings"]
        assert set(spec["bindings"]["Observation.status"]) == {"active", "active-trial", "inactive"}
        assert len(spec["slices"]) == 1
        # SBPCode qualifier must be stripped from subpath
        matcher_key = next(iter(spec["slices"][0]["matchers"].keys()))
        assert matcher_key == "code.coding.code"

    def test_null_safety_and_snapshot_narrowing(self, tmp_path: Path) -> None:
        sd_file = tmp_path / "nulls_sd.json"
        sd_file.write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/null-safe",
                    "kind": "resource",
                    "type": "Observation",
                    "derivation": "constraint",
                    "differential": None,
                    "snapshot": {
                        "element": [
                            {
                                "id": "Observation.status",
                                "path": "Observation.status",
                                "min": 1,
                                "binding": None,
                                "type": None,
                            },
                            {
                                "id": "Observation.value[x]",
                                "path": "Observation.value[x]",
                                "type": [{"code": "Quantity"}],
                            },
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
        clear_ig_cache()
        raw = load_raw_ig_profiles([sd_file])
        assert "http://example.org/sd/null-safe" in raw
        narrowing = raw["http://example.org/sd/null-safe"]["type_narrowing"]
        assert narrowing["Observation.value[x]"] == ["Quantity"]

    def test_load_from_directory_and_package_subdir(self, tmp_path: Path) -> None:
        ig_dir = tmp_path / "my_ig"
        pkg_subdir = ig_dir / "package"
        pkg_subdir.mkdir(parents=True)
        (pkg_subdir / "sd1.json").write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/in-dir",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "differential": {
                        "element": [{"id": "Patient.name", "path": "Patient.name", "min": 1}]
                    },
                }
            ),
            encoding="utf-8",
        )
        clear_ig_cache()
        raw = load_raw_ig_profiles([ig_dir])
        assert "http://example.org/sd/in-dir" in raw

    def test_load_from_tarball_with_security_and_limits(self, tmp_path: Path) -> None:
        tgz_file = tmp_path / "ig.tgz"
        with tarfile.open(tgz_file, "w:gz") as tar:
            # 1. Normal JSON
            diff_el = [{"id": "Patient.telecom", "path": "Patient.telecom", "min": 1}]
            data1 = json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/in-tar",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "differential": {"element": diff_el},
                }
            ).encode("utf-8")
            ti1 = tarfile.TarInfo(name="package/sd1.json")
            ti1.size = len(data1)
            tar.addfile(ti1, io.BytesIO(data1))

            # 2. Path traversal attack member (ZipSlip) -> should be skipped safely
            ti_bad = tarfile.TarInfo(name="../../etc/passwd.json")
            ti_bad.size = len(b"{}")
            tar.addfile(ti_bad, io.BytesIO(b"{}"))

            # 3. Non-json file
            ti_txt = tarfile.TarInfo(name="package/readme.txt")
            ti_txt.size = len(b"hello")
            tar.addfile(ti_txt, io.BytesIO(b"hello"))

        clear_ig_cache()
        raw = load_raw_ig_profiles([tgz_file])
        assert "http://example.org/sd/in-tar" in raw

    def test_tarball_oversized_and_member_limit(self, tmp_path: Path) -> None:
        # Member limit > 5000 test
        tgz_huge = tmp_path / "huge.tgz"
        with tarfile.open(tgz_huge, "w:gz") as tar:
            for i in range(5002):
                ti = tarfile.TarInfo(name=f"f{i}.json")
                ti.size = 2
                tar.addfile(ti, io.BytesIO(b"{}"))

        with pytest.raises(ValueError, match="Tarball exceeds maximum member limit"):
            load_raw_ig_profiles([tgz_huge])

    def test_cached_package_semver_sorting(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_cache = tmp_path / ".fhir" / "packages"
        v1_2 = fake_cache / "hl7.fhir.uv.ips#1.2.0" / "package"
        v1_10 = fake_cache / "hl7.fhir.uv.ips#1.10.0" / "package"
        v1_2.mkdir(parents=True)
        v1_10.mkdir(parents=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        # Resolving without version must pick 1.10.0 over 1.2.0 due to semver tuple key
        resolved = _find_cached_package("hl7.fhir.uv.ips")
        assert resolved is not None
        assert "1.10.0" in str(resolved)

        # Resolving with specific version
        resolved_exact = _find_cached_package("hl7.fhir.uv.ips#1.2.0")
        assert resolved_exact is not None
        assert "1.2.0" in str(resolved_exact)

    def test_cache_invalidation_and_defensive_copies(self, tmp_path: Path) -> None:
        sd_file = tmp_path / "test-sd.json"
        diff_name = [{"id": "Patient.name", "path": "Patient.name", "min": 1}]
        sd_file.write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/cached-test",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "differential": {"element": diff_name},
                }
            ),
            encoding="utf-8",
        )

        clear_ig_cache()
        map1 = load_compiled_ig_profiles([sd_file])
        assert "http://example.org/sd/cached-test" in map1

        # Defensive copy isolation: modifying returned dict doesn't modify cache
        map1["mutated_key"] = None  # type: ignore[assignment]
        map2 = load_compiled_ig_profiles([sd_file])
        assert "mutated_key" not in map2

        # Invalidate by updating file content
        sd_file.write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/cached-test",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {"id": "Patient.name", "path": "Patient.name", "min": 1},
                            {"id": "Patient.telecom", "path": "Patient.telecom", "min": 1},
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )
        map3 = load_compiled_ig_profiles([sd_file])
        prof = map3["http://example.org/sd/cached-test"]
        req_paths = {r.path for r in prof.required}
        assert "Patient.telecom" in req_paths

    def test_register_ig(self, tmp_path: Path) -> None:
        sd_file = tmp_path / "global_reg.json"
        diff_reg = [{"id": "Patient.name", "path": "Patient.name", "min": 1}]
        sd_file.write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/globally-registered",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "differential": {"element": diff_reg},
                }
            ),
            encoding="utf-8",
        )
        res = register_ig([sd_file])
        assert "http://example.org/sd/globally-registered" in res
        assert "http://example.org/sd/globally-registered" in COMPILED_PROFILES


# ==============================================================================
# SECTION 3: Intra-File Parallelism
# ==============================================================================


class TestIntraFileParallelism:
    def test_single_ndjson_file_parallel_exact_equality(self, tmp_path: Path) -> None:
        ndjson_file = tmp_path / "batch.ndjson"
        valid_res = _valid_patient_dict()
        invalid_res = _invalid_patient_dict()

        # Build 20 lines with known sequence
        lines = []
        for i in range(10):
            lines.append(json.dumps({**valid_res, "id": f"valid-{i}"}))
            lines.append(json.dumps({**invalid_res, "id": f"invalid-{i}"}))
        ndjson_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

        res_seq = validate_dataset(ndjson_file, parallel=False)
        res_par = validate_dataset(ndjson_file, parallel=True)

        assert res_seq["total_resources"] == 20
        assert res_seq["valid_resources"] == 10
        assert res_seq["invalid_resources"] == 10
        assert res_seq["compliance_rate"] == 50.0

        # Exact match of counts, compliance, and issues list
        assert res_par["total_resources"] == res_seq["total_resources"]
        assert res_par["valid_resources"] == res_seq["valid_resources"]
        assert res_par["invalid_resources"] == res_seq["invalid_resources"]
        assert res_par["compliance_rate"] == res_seq["compliance_rate"]
        assert res_par["issues"] == res_seq["issues"]

    def test_single_bundle_file_parallel_exact_equality(self, tmp_path: Path) -> None:
        bundle_file = tmp_path / "batch_bundle.json"
        valid_res = _valid_patient_dict()
        invalid_res = _invalid_patient_dict()

        entries = []
        for i in range(8):
            entries.append({"resource": {**valid_res, "id": f"b-valid-{i}"}})
            entries.append({"resource": {**invalid_res, "id": f"b-invalid-{i}"}})

        bundle_file.write_text(
            json.dumps({"resourceType": "Bundle", "type": "collection", "entry": entries}),
            encoding="utf-8",
        )

        res_seq = validate_dataset(bundle_file, parallel=False)
        res_par = validate_dataset(bundle_file, parallel=True)

        assert res_seq["total_resources"] == 16
        assert res_seq["valid_resources"] == 8
        assert res_seq["invalid_resources"] == 8
        assert res_par["issues"] == res_seq["issues"]

    def test_single_file_edge_cases(self, tmp_path: Path) -> None:
        empty_ndjson = tmp_path / "empty.ndjson"
        empty_ndjson.write_text("", encoding="utf-8")
        assert validate_dataset(empty_ndjson, parallel=True)["total_resources"] == 0

        one_line = tmp_path / "one.ndjson"
        one_line.write_text(json.dumps(_valid_patient_dict()), encoding="utf-8")
        assert validate_dataset(one_line, parallel=True)["valid_resources"] == 1

        empty_bundle = tmp_path / "empty_bundle.json"
        empty_bundle.write_text(
            json.dumps({"resourceType": "Bundle", "type": "collection", "entry": []}),
            encoding="utf-8",
        )
        assert validate_dataset(empty_bundle, parallel=True)["total_resources"] == 0

    def test_eager_ig_loading_fails_early_on_missing_path(self, tmp_path: Path) -> None:
        valid_file = tmp_path / "test.json"
        valid_file.write_text(json.dumps(_valid_patient_dict()), encoding="utf-8")
        with pytest.raises(FileNotFoundError, match="IG source not found"):
            validate_dataset(valid_file, ig_sources=["non_existent_ig.tgz"])


# ==============================================================================
# SECTION 4: CLI Integration Tests
# ==============================================================================


class TestCLIIntegration:
    def test_cli_formats_and_output_flags(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        patient_file = tmp_path / "patient.json"
        patient_file.write_text(json.dumps(_valid_patient_dict()), encoding="utf-8")

        # 1. Default text format
        assert cli_main([str(patient_file)]) == 0
        out_text = capsys.readouterr().out
        assert "Validated 1 resource(s)" in out_text

        # 2. --format json
        assert cli_main([str(patient_file), "--format", "json"]) == 0
        json_data = json.loads(capsys.readouterr().out)
        assert json_data["total_resources"] == 1
        assert json_data["valid_resources"] == 1

        # 3. --operation-outcome flag
        assert cli_main([str(patient_file), "--operation-outcome"]) == 0
        oo_data = json.loads(capsys.readouterr().out)
        assert oo_data["resourceType"] == "OperationOutcome"
        assert validate_resource(oo_data, require_canadian_profile=False) == []

        # 4. --format sarif
        assert cli_main([str(patient_file), "--format", "sarif"]) == 0
        sarif_data = json.loads(capsys.readouterr().out)
        assert sarif_data["version"] == "2.1.0"

        # 5. --format junit to -o output file
        junit_out = tmp_path / "results.xml"
        assert cli_main([str(patient_file), "--format", "junit", "-o", str(junit_out)]) == 0
        assert junit_out.exists()
        xml_root = xml_fromstring(junit_out.read_text(encoding="utf-8"))
        assert xml_root.tag == "testsuites"

    def test_cli_with_ig_source(self, tmp_path: Path) -> None:
        sd_file = tmp_path / "custom_sd.json"
        diff_gender = [{"id": "Patient.gender", "path": "Patient.gender", "max": "0"}]
        sd_file.write_text(
            json.dumps(
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/sd/cli-test",
                    "kind": "resource",
                    "type": "Patient",
                    "derivation": "constraint",
                    "differential": {"element": diff_gender},
                }
            ),
            encoding="utf-8",
        )
        patient_file = tmp_path / "patient.json"
        patient_file.write_text(
            json.dumps({"resourceType": "Patient", "gender": "female"}),
            encoding="utf-8",
        )

        exit_code = cli_main(
            [
                str(patient_file),
                "--no-canadian",
                "-ig",
                str(sd_file),
                "--profile",
                "http://example.org/sd/cli-test",
            ]
        )
        assert exit_code == 1

    def test_cli_missing_target_exits_code_2(self, capsys: pytest.CaptureFixture[str]) -> None:
        ret = cli_main(["non_existent_file_xyz.json"])
        assert ret == 2
        err = capsys.readouterr().err
        assert "Error: Path not found" in err


# ==============================================================================
# SECTION 5: Coverage Deep Dives (Edge Cases & Missing Branches)
# ==============================================================================


class TestCoverageDeepDives:
    def test_dataset_read_errors_and_multi_file_parallel(self, tmp_path: Path) -> None:
        opts = _ValidationOptions()
        # 1. Non-json/ndjson file returns 0, 0, []
        txt_file = tmp_path / "notes.txt"
        txt_file.write_text("hello", encoding="utf-8")
        assert _validate_file(str(txt_file), opts) == (0, 0, [])
        assert _validate_file_parallel(str(txt_file), opts) == (0, 0, [])

        # 2. Corrupt JSON file in _validate_json_file
        bad_json = tmp_path / "bad.json"
        bad_json.write_text("{not valid json", encoding="utf-8")
        tot, val, issues = _validate_json_file(bad_json, opts)
        assert tot == 0
        assert val == 0
        assert "error" in issues[0]

        # 3. Corrupt JSON in _validate_json_file_parallel
        tot_p, _val_p, issues_p = _validate_file_parallel(str(bad_json), opts)
        assert tot_p == 0
        assert "error" in issues_p[0]

        # 4. Multi-file dataset with parallel=True (len(files) > 1 branch)
        f1 = tmp_path / "f1.json"
        f2 = tmp_path / "f2.json"
        f1.write_text(json.dumps(_valid_patient_dict()), encoding="utf-8")
        f2.write_text(json.dumps(_valid_patient_dict()), encoding="utf-8")
        dir_res = validate_dataset(tmp_path, parallel=True)
        assert dir_res["total_resources"] >= 2

        # 5. NDJSON with invalid JSON line in parallel mode
        bad_ndjson = tmp_path / "corrupt_line.ndjson"
        bad_ndjson.write_text('{"resourceType": "Patient"}\n{bad json line\n', encoding="utf-8")
        tot_nd, _val_nd, issues_nd = _validate_file_parallel(str(bad_ndjson), opts)
        assert tot_nd == 2
        assert any(i.get("line") == 2 for i in issues_nd)

        # 6. NDJSON file read error (e.g. unreadable path)
        unreadable = tmp_path / "does_not_exist.ndjson"
        tot_un, _val_un, issues_un = _validate_ndjson_file(unreadable, opts)
        assert tot_un == 0
        assert len(issues_un) == 1

        tot_un_p, _val_un_p, issues_un_p = _validate_file_parallel(str(unreadable), opts)
        assert tot_un_p == 0
        assert len(issues_un_p) == 1

    def test_ig_loader_inheritance_and_cycles(self, tmp_path: Path) -> None:
        # Base SD with extensive differential
        base_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/parent",
            "kind": "resource",
            "type": "Patient",
            "derivation": "constraint",
            "differential": {
                "element": [
                    {"id": "Patient.name", "path": "Patient.name", "min": 1},
                    {"id": "Patient.gender", "path": "Patient.gender", "max": "0"},
                    {"id": "Patient.active", "path": "Patient.active", "max": "1"},
                    {"id": "Patient.telecom", "path": "Patient.telecom", "fixedString": "tel"},
                    {
                        "id": "Patient.identifier",
                        "path": "Patient.identifier",
                        "patternString": "pat",
                    },
                    {
                        "id": "Patient.deceased[x]",
                        "path": "Patient.deceased[x]",
                        "type": [{"code": "boolean"}],
                    },
                    {
                        "id": "Patient.generalPractitioner",
                        "path": "Patient.generalPractitioner",
                        "type": [
                            {
                                "code": "Reference",
                                "targetProfile": [
                                    "http://hl7.org/fhir/StructureDefinition/Practitioner"
                                ],
                            }
                        ],
                    },
                    {
                        "id": "Patient.language",
                        "path": "Patient.language",
                        "binding": {
                            "strength": "required",
                            "valueSet": "http://example.org/vs/lang",
                        },
                    },
                    {
                        "id": "Patient.contact:emergency",
                        "path": "Patient.contact",
                        "min": 1,
                        "max": "2",
                    },
                    {
                        "id": "Patient.contact:emergency.relationship",
                        "path": "Patient.contact.relationship",
                        "fixedCode": "EM",
                    },
                ]
            },
        }

        # Child SD inheriting from parent
        child_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/child",
            "kind": "resource",
            "type": "Patient",
            "derivation": "constraint",
            "baseDefinition": "http://example.org/sd/parent|2.0",
            "differential": {
                "element": [
                    {"id": "Patient.birthDate", "path": "Patient.birthDate", "min": 1},
                ]
            },
        }

        vs = {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/lang",
            "compose": {"include": [{"concept": [{"code": "en"}, {"code": "fr"}]}]},
        }

        ignored_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/ignored",
            "kind": "logical",
            "derivation": "specialization",
        }

        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": base_sd},
                {"resource": child_sd},
                {"resource": vs},
                {"resource": ignored_sd},
            ],
        }
        b_file = tmp_path / "inheritance_bundle.json"
        b_file.write_text(json.dumps(bundle), encoding="utf-8")

        clear_ig_cache()
        raw = load_raw_ig_profiles([b_file])
        assert "http://example.org/sd/ignored" not in raw
        assert "http://example.org/sd/child" in raw
        child_prof = raw["http://example.org/sd/child"]

        assert "Patient.name" in child_prof["required"]
        assert "Patient.birthDate" in child_prof["required"]
        assert "Patient.gender" in child_prof["forbidden"]
        assert "Patient.active" in child_prof["max_one"]
        assert child_prof["fixed"]["Patient.telecom"] == "tel"
        assert child_prof["pattern"]["Patient.identifier"] == "pat"
        assert child_prof["type_narrowing"]["Patient.deceased[x]"] == ["boolean"]
        assert child_prof["target_types"]["Patient.generalPractitioner"] == ["Practitioner"]
        assert child_prof["bindings"]["Patient.language"] == ["en", "fr"]
        assert len(child_prof["slices"]) == 1

        # Test cycle detection: A -> B -> A
        cycle_a = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/cycleA",
            "kind": "resource",
            "derivation": "constraint",
            "baseDefinition": "http://example.org/sd/cycleB",
            "differential": {"element": [{"id": "P.x", "path": "P.x", "min": 1}]},
        }
        cycle_b = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/cycleB",
            "kind": "resource",
            "derivation": "constraint",
            "baseDefinition": "http://example.org/sd/cycleA",
            "differential": {"element": [{"id": "P.y", "path": "P.y", "min": 1}]},
        }
        cycle_file = tmp_path / "cycle.json"
        cycle_file.write_text(
            json.dumps(
                {
                    "resourceType": "Bundle",
                    "entry": [{"resource": cycle_a}, {"resource": cycle_b}],
                }
            ),
            encoding="utf-8",
        )
        clear_ig_cache()
        raw_cycle = load_raw_ig_profiles([cycle_file])
        assert "http://example.org/sd/cycleA" in raw_cycle

    def test_ig_loader_snapshot_diff_and_base_elements(self, tmp_path: Path) -> None:
        base_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/snap-base",
            "kind": "resource",
            "type": "Observation",
            "derivation": "constraint",
            "snapshot": {
                "element": [
                    {
                        "id": "Observation.status",
                        "path": "Observation.status",
                        "min": 0,
                        "max": "*",
                        "fixedCode": "A",
                        "patternCode": "P",
                    },
                ]
            },
        }
        derived_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/snap-derived",
            "kind": "resource",
            "type": "Observation",
            "derivation": "constraint",
            "baseDefinition": "http://example.org/sd/snap-base",
            "differential": None,
            "snapshot": {
                "element": [
                    {
                        "id": "Observation.status",
                        "path": "Observation.status",
                        "min": 1,
                        "max": "1",
                        "fixedCode": "B",
                        "patternCode": "Q",
                        "binding": {
                            "strength": "required",
                            "valueSet": "http://example.org/vs/snap-vs",
                        },
                    },
                    {
                        "id": "Observation.note",
                        "path": "Observation.note",
                        "max": "0",
                    },
                    {
                        "id": "Observation.value[x]",
                        "path": "Observation.value[x]",
                        "type": [{"code": "Quantity"}, {"code": "string"}],
                    },
                ]
            },
        }
        vs = {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/snap-vs",
            "compose": {"include": [{"concept": [{"code": "val1"}]}]},
        }
        snap_bundle = tmp_path / "snap_bundle.json"
        snap_bundle.write_text(
            json.dumps(
                {
                    "resourceType": "Bundle",
                    "entry": [
                        {"resource": base_sd},
                        {"resource": derived_sd},
                        {"resource": vs},
                    ],
                }
            ),
            encoding="utf-8",
        )
        clear_ig_cache()
        raw = load_raw_ig_profiles([snap_bundle])
        assert "http://example.org/sd/snap-derived" in raw
        prof = raw["http://example.org/sd/snap-derived"]
        assert "Observation.status" in prof["required"]
        assert "Observation.status" in prof["max_one"]
        assert "Observation.note" in prof["forbidden"]
        assert prof["fixed"]["Observation.status"] == "B"
        assert prof["pattern"]["Observation.status"] == "Q"
        assert prof["bindings"]["Observation.status"] == ["val1"]
        assert prof["type_narrowing"]["Observation.value[x]"] == ["Quantity", "string"]

    def test_ig_loader_nested_value_sets_and_code_systems(self, tmp_path: Path) -> None:
        cs = {
            "resourceType": "CodeSystem",
            "url": "http://example.org/cs/nested",
            "concept": [
                {
                    "code": "lvl1",
                    "concept": [{"code": "lvl2", "concept": [{"code": "lvl3"}]}],
                }
            ],
        }
        vs_expansion = {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/expansion-nested",
            "expansion": {
                "contains": [
                    {
                        "code": "exp1",
                        "contains": [{"code": "exp2", "contains": [{"code": "exp3"}]}],
                    }
                ]
            },
        }
        vs_filter = {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/with-filter",
            "compose": {
                "include": [
                    {
                        "system": "http://example.org/cs/nested",
                        "filter": [{"property": "concept", "op": "is-a", "value": "x"}],
                    }
                ]
            },
        }
        b_file = tmp_path / "vs_cs_bundle.json"
        b_file.write_text(
            json.dumps(
                {
                    "resourceType": "Bundle",
                    "entry": [
                        {"resource": cs},
                        {"resource": vs_expansion},
                        {"resource": vs_filter},
                    ],
                }
            ),
            encoding="utf-8",
        )
        clear_ig_cache()
        raw = load_raw_ig_profiles([b_file])
        assert "http://example.org/cs/nested" not in raw

    def test_ig_loader_tarball_and_file_edge_cases(self, tmp_path: Path) -> None:
        tgz_file = tmp_path / "edge_cases.tgz"
        with tarfile.open(tgz_file, "w:gz") as tar:
            # 1. Directory member
            ti_dir = tarfile.TarInfo(name="package/subdir")
            ti_dir.type = tarfile.DIRTYPE
            tar.addfile(ti_dir)

            # 2. Corrupt JSON
            data_bad = b"{invalid json"
            ti_bad = tarfile.TarInfo(name="package/corrupt.json")
            ti_bad.size = len(data_bad)
            tar.addfile(ti_bad, io.BytesIO(data_bad))

            # 3. JSON array instead of dict
            data_arr = b"[1, 2, 3]"
            ti_arr = tarfile.TarInfo(name="package/array.json")
            ti_arr.size = len(data_arr)
            tar.addfile(ti_arr, io.BytesIO(data_arr))

        clear_ig_cache()
        raw = load_raw_ig_profiles([tgz_file])
        assert raw == {}

        # Direct file with corrupt JSON and array JSON
        corrupt_f = tmp_path / "corrupt_single.json"
        corrupt_f.write_text("{bad json", encoding="utf-8")
        clear_ig_cache()
        assert load_raw_ig_profiles([corrupt_f]) == {}

        arr_f = tmp_path / "array_single.json"
        arr_f.write_text("[1, 2, 3]", encoding="utf-8")
        clear_ig_cache()
        assert load_raw_ig_profiles([arr_f]) == {}

        # Directory with corrupt JSON and directory without json files
        d = tmp_path / "empty_dir"
        d.mkdir()
        clear_ig_cache()
        assert load_raw_ig_profiles([d]) == {}

        fp_dir = _fingerprint_source(d)
        assert fp_dir[2] == 0

        fp_nonexist = _fingerprint_source(tmp_path / "ghost_file")
        assert fp_nonexist[1] == 0

    def test_cached_package_fallbacks(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_cache = tmp_path / ".fhir" / "packages"
        dir_only = fake_cache / "custom.pkg#2.0.0"
        dir_only.mkdir(parents=True)

        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        res_exact = _find_cached_package("custom.pkg#2.0.0")
        assert res_exact == dir_only

        res_glob = _find_cached_package("custom.pkg")
        assert res_glob == dir_only

        monkeypatch.setattr(Path, "home", lambda: tmp_path / "empty_home")
        assert _find_cached_package("custom.pkg") is None

    def test_formatters_uncovered_branches(self) -> None:
        expr = _extract_expression("Structural[Patient.name]: missing", None)
        assert expr == ["Patient.name"]
        assert (
            _format_diagnostics("Patient: field missing", "Patient", None)
            == "Patient: field missing"
        )
        assert (
            _format_diagnostics("Patient/p1: field missing", "Patient", "p1")
            == "Patient/p1: field missing"
        )
        assert _format_diagnostics("field missing", "Patient", None) == "Patient: field missing"
        assert _classify_sarif_rule_id("Address[0] state US-only") == "FHIR004-Canadian"
        assert _classify_sarif_rule_id("not in required ValueSet") == "FHIR003-Profile"

    def test_direct_batch_and_chunk_workers(self) -> None:
        opts = _ValidationOptions()
        # Direct _validate_resource_batch call
        tot, val, issues = _validate_resource_batch(
            ([_valid_patient_dict(), _invalid_patient_dict()], "batch.json", opts)
        )
        assert tot == 2
        assert val == 1
        assert len(issues) == 1

        # Direct _validate_ndjson_chunk call with valid and invalid lines
        chunk_items = [
            (1, json.dumps(_valid_patient_dict())),
            (2, "{corrupt line"),
            (3, json.dumps(_invalid_patient_dict())),
        ]
        tot_c, val_c, issues_c = _validate_ndjson_chunk((chunk_items, "test.ndjson", opts))
        assert tot_c == 3
        assert val_c == 1
        assert len(issues_c) == 2

    def test_ig_loader_additional_branches(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # 1. Profile inheriting directly from PROFILE_CONSTRAINTS
        child_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/ca-child",
            "kind": "resource",
            "type": "Patient",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient",
            "differential": {
                "element": [{"id": "Patient.gender", "path": "Patient.gender", "min": 1}]
            },
        }
        child_file = tmp_path / "ca_child.json"
        child_file.write_text(json.dumps(child_sd), encoding="utf-8")
        clear_ig_cache()
        raw = load_raw_ig_profiles([child_file])
        assert "http://example.org/sd/ca-child" in raw
        assert "Patient.identifier.system" in raw["http://example.org/sd/ca-child"]["required"]
        assert "Patient.gender" in raw["http://example.org/sd/ca-child"]["required"]

        # 2. Tarball member exceeding bytes limit
        tgz_file = tmp_path / "oversized.tgz"
        with tarfile.open(tgz_file, "w:gz") as tar:
            data = b'{"resourceType": "StructureDefinition"}'
            ti = tarfile.TarInfo(name="package/large.json")
            ti.size = len(data)
            tar.addfile(ti, io.BytesIO(data))

        monkeypatch.setattr(igl, "_MAX_TAR_MEMBER_BYTES", 5)
        clear_ig_cache()
        assert load_raw_ig_profiles([tgz_file]) == {}

        # 3. Directory with corrupt JSON file
        corrupt_dir = tmp_path / "corrupt_dir"
        corrupt_dir.mkdir()
        (corrupt_dir / "bad.json").write_text("{bad json", encoding="utf-8")
        (corrupt_dir / "arr.json").write_text("[1, 2]", encoding="utf-8")
        clear_ig_cache()
        assert load_raw_ig_profiles([corrupt_dir]) == {}

        # 4. _fingerprint_source on dir with package subdir containing files
        pkg_d = tmp_path / "pkg_tree"
        (pkg_d / "package").mkdir(parents=True)
        (pkg_d / "package" / "f.json").write_text("{}", encoding="utf-8")
        fp = _fingerprint_source(pkg_d)
        assert fp[2] > 0

    def test_cli_main_module_run(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(sys, "argv", ["fhirlance", "--help"])
        sys.modules.pop("fhirlance.cli", None)
        with pytest.raises(SystemExit) as exc:
            runpy.run_module("fhirlance.cli", run_name="__main__")
        assert exc.value.code == 0


class TestPerformanceAndReliabilityPolish:
    """Regression tests for performance optimizations and reliability fixes."""

    def test_ig_sources_single_fingerprint_on_bundle_and_dataset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/single-fp-patient",
            "kind": "resource",
            "type": "Patient",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient",
            "differential": {
                "element": [{"id": "Patient.gender", "path": "Patient.gender", "min": 1}]
            },
        }
        ig_dir = tmp_path / "custom_ig"
        ig_dir.mkdir()
        (ig_dir / "sd.json").write_text(json.dumps(sd), encoding="utf-8")

        # 1. Multi-entry Bundle with validate_resource
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": _valid_patient_dict()},
                {"resource": _valid_patient_dict()},
                {"resource": _valid_patient_dict()},
            ],
        }

        clear_ig_cache()
        call_count = 0
        orig_fp = igl._fingerprint_source

        def spy_fp(path: Path) -> tuple[str, int, int]:
            nonlocal call_count
            call_count += 1
            return orig_fp(path)

        monkeypatch.setattr(igl, "_fingerprint_source", spy_fp)

        issues = validate_resource(bundle, ig_sources=[ig_dir])
        assert not issues
        assert call_count == 1, f"Expected 1 fingerprint call, got {call_count}"

        # 2. Multi-line NDJSON with validate_dataset
        ndjson_file = tmp_path / "patients.ndjson"
        ndjson_file.write_text(
            "\n".join(json.dumps(_valid_patient_dict()) for _ in range(5)),
            encoding="utf-8",
        )

        clear_ig_cache()
        call_count = 0
        rep = validate_dataset(ndjson_file, ig_sources=[ig_dir])
        assert rep["total_resources"] == 5
        assert rep["valid_resources"] == 5
        assert call_count == 1, f"Expected 1 fingerprint call, got {call_count}"

        # 3. Direct dictionary passed as ig_sources to validate_resource
        compiled_map = load_compiled_ig_profiles([ig_dir])
        call_count = 0
        issues_dict = validate_resource(bundle, ig_sources=compiled_map)
        assert not issues_dict
        assert call_count == 0, "Passing compiled dict directly should incur 0 fingerprint calls"

    def test_cli_exit_code_on_corrupt_json(self, tmp_path: Path) -> None:
        bad_file = tmp_path / "broken.json"
        bad_file.write_text("{bad json not valid", encoding="utf-8")
        exit_code = cli_main([str(bad_file)])
        assert exit_code == 1

    def test_clear_ig_cache_resets_compiled_profiles(self, tmp_path: Path) -> None:
        custom_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/sd/registered-clean-test",
            "kind": "resource",
            "type": "Patient",
            "derivation": "constraint",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
            "differential": {
                "element": [{"id": "Patient.active", "path": "Patient.active", "min": 1}]
            },
        }
        custom_file = tmp_path / "reg_profile.json"
        custom_file.write_text(json.dumps(custom_sd), encoding="utf-8")

        registered = register_ig([custom_file])
        assert "http://example.org/sd/registered-clean-test" in registered
        assert "http://example.org/sd/registered-clean-test" in COMPILED_PROFILES

        clear_ig_cache()
        assert "http://example.org/sd/registered-clean-test" not in COMPILED_PROFILES
        assert (
            "http://hl7.org/fhir/ca/baseline/StructureDefinition/profile-patient"
            in COMPILED_PROFILES
        )

    def test_tarball_member_limit_lazy_streaming(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        tgz_file = tmp_path / "limit_test.tgz"
        with tarfile.open(tgz_file, "w:gz") as tar:
            for idx in range(3):
                data = b'{"resourceType": "StructureDefinition"}'
                ti = tarfile.TarInfo(name=f"package/sd_{idx}.json")
                ti.size = len(data)
                tar.addfile(ti, io.BytesIO(data))

        monkeypatch.setattr(igl, "_MAX_TAR_MEMBERS", 2)
        clear_ig_cache()
        with pytest.raises(ValueError, match="Tarball exceeds maximum member limit of 2"):
            load_raw_ig_profiles([tgz_file])

    def test_cpu_aware_workers_fallback(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(os, "cpu_count", lambda: None)

        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": _valid_patient_dict()} for _ in range(8)],
        }
        b_file = tmp_path / "bundle_cpu.json"
        b_file.write_text(json.dumps(bundle), encoding="utf-8")

        opts = _ValidationOptions()
        tot, val, issues = _validate_json_file_parallel(b_file, opts)
        assert tot == 8
        assert val == 8
        assert not issues

        nd_file = tmp_path / "ndjson_cpu.ndjson"
        nd_file.write_text(
            "\n".join(json.dumps(_valid_patient_dict()) for _ in range(8)),
            encoding="utf-8",
        )
        tot_nd, val_nd, issues_nd = _validate_ndjson_file_parallel(nd_file, opts)
        assert tot_nd == 8
        assert val_nd == 8
        assert not issues_nd
