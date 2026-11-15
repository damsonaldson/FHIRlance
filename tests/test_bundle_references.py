"""Tests for FHIR R4 Bundle invariants, reference resolution, targetProfile, and aggregation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fhirlance.dataset import validate_dataset
from fhirlance.ig_loader import load_compiled_ig_bundle
from fhirlance.profile_engine import CompiledProfile, compile_profiles
from fhirlance.resource_validator import validate_resource

# ==============================================================================
# Helpers
# ==============================================================================


def _valid_patient(
    rid: str = "pat-1",
    *,
    family: str = "Doe",
    managing_org: dict[str, Any] | None = None,
    contained: list[dict[str, Any]] | None = None,
    profiles: list[str] | None = None,
) -> dict[str, Any]:
    res: dict[str, Any] = {
        "resourceType": "Patient",
        "id": rid,
        "name": [{"family": family, "given": ["Jane"]}],
    }
    if managing_org is not None:
        res["managingOrganization"] = managing_org
    if contained is not None:
        res["contained"] = contained
    if profiles is not None:
        res["meta"] = {"profile": profiles}
    return res


def _valid_composition() -> dict[str, Any]:
    return {
        "resourceType": "Composition",
        "id": "comp-1",
        "status": "final",
        "type": {"coding": [{"system": "http://loinc.org", "code": "11502-2"}]},
        "date": "2026-01-01",
        "author": [{"reference": "Practitioner/prac-1"}],
        "title": "Clinical Summary",
    }


def _valid_message_header() -> dict[str, Any]:
    return {
        "resourceType": "MessageHeader",
        "id": "mh-1",
        "eventCoding": {"system": "http://example.org/events", "code": "notify"},
        "source": {"endpoint": "http://example.org/source"},
    }


def _compile_one(url: str, spec: dict[str, Any]) -> dict[str, CompiledProfile]:
    return compile_profiles({url: spec})


def _make_sd_package(tmp_path: Path, sds: list[dict[str, Any]]) -> Path:
    pkg_dir = tmp_path / "test-ref-ig"
    pkg_dir.mkdir()
    (pkg_dir / "package.json").write_text(
        json.dumps({"name": "test.ref.ig", "version": "1.0.0", "fhirVersion": "4.0.1"}),
        encoding="utf-8",
    )
    for idx, sd in enumerate(sds):
        (pkg_dir / f"StructureDefinition-{idx}.json").write_text(json.dumps(sd), encoding="utf-8")
    return pkg_dir


# ==============================================================================
# 1. Bundle Invariants (bdl-2, bdl-5, bdl-8, bdl-9, bdl-10, bdl-11, bdl-12)
# ==============================================================================


class TestBundleInvariants:
    def test_bdl_2_search_only_in_searchset(self) -> None:
        valid = {
            "resourceType": "Bundle",
            "type": "searchset",
            "entry": [
                {
                    "fullUrl": "urn:uuid:pat-1",
                    "resource": _valid_patient(),
                    "search": {"mode": "match"},
                }
            ],
        }
        assert validate_resource(valid) == []

        invalid = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:pat-1",
                    "resource": _valid_patient(),
                    "search": {"mode": "match"},
                }
            ],
        }
        issues = validate_resource(invalid)
        assert any("Invariant[bdl-2]" in i for i in issues)

    def test_bdl_5_entry_must_have_resource_request_or_response(self) -> None:
        valid = {
            "resourceType": "Bundle",
            "type": "transaction",
            "entry": [
                {
                    "fullUrl": "urn:uuid:pat-1",
                    "request": {"method": "GET", "url": "Patient"},
                }
            ],
        }
        assert validate_resource(valid) == []

        invalid = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"fullUrl": "urn:uuid:pat-1"}],
        }
        issues = validate_resource(invalid)
        assert any("Invariant[bdl-5]" in i for i in issues)

    def test_bdl_8_full_url_must_not_contain_history(self) -> None:
        valid = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "https://example.org/fhir/Patient/pat-1",
                    "resource": _valid_patient(),
                }
            ],
        }
        assert validate_resource(valid) == []

        invalid = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "https://example.org/fhir/Patient/pat-1/_history/1",
                    "resource": _valid_patient(),
                }
            ],
        }
        issues = validate_resource(invalid)
        assert any("Invariant[bdl-8]" in i for i in issues)

    def test_bdl_9_10_11_document_bundle(self) -> None:
        valid_doc = {
            "resourceType": "Bundle",
            "type": "document",
            "identifier": {"system": "urn:ietf:rfc:3986", "value": "urn:uuid:doc-1"},
            "timestamp": "2026-01-01T00:00:00Z",
            "entry": [
                {"fullUrl": "urn:uuid:comp-1", "resource": _valid_composition()},
            ],
        }
        assert validate_resource(valid_doc) == []

        bad_doc = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [
                {"fullUrl": "urn:uuid:pat-1", "resource": _valid_patient()},
            ],
        }
        issues = validate_resource(bad_doc)
        assert any("Invariant[bdl-9]" in i for i in issues)
        assert any("Invariant[bdl-10]" in i for i in issues)
        assert any("Invariant[bdl-11]" in i for i in issues)

    def test_bdl_12_message_bundle(self) -> None:
        valid_msg = {
            "resourceType": "Bundle",
            "type": "message",
            "entry": [
                {"fullUrl": "urn:uuid:mh-1", "resource": _valid_message_header()},
            ],
        }
        assert validate_resource(valid_msg) == []

        bad_msg = {
            "resourceType": "Bundle",
            "type": "message",
            "entry": [
                {"fullUrl": "urn:uuid:pat-1", "resource": _valid_patient()},
            ],
        }
        issues = validate_resource(bad_msg)
        assert any("Invariant[bdl-12]" in i for i in issues)


# ==============================================================================
# 2. Outer Bundle Validation in validate_dataset() (Serial & Parallel)
# ==============================================================================


class TestDatasetOuterBundleValidation:
    @pytest.mark.parametrize("parallel", [False, True])
    def test_valid_outer_bundle_preserves_entry_count(self, tmp_path: Path, parallel: bool) -> None:
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"fullUrl": "urn:uuid:p1", "resource": _valid_patient("p1")},
                {"fullUrl": "urn:uuid:p2", "resource": _valid_patient("p2", family="Smith")},
            ],
        }
        f = tmp_path / "valid_bundle.json"
        f.write_text(json.dumps(bundle), encoding="utf-8")

        report = validate_dataset(f, parallel=parallel)
        assert report["total_resources"] == 2
        assert report["valid_resources"] == 2
        assert report["invalid_resources"] == 0
        assert report["issues"] == []

    @pytest.mark.parametrize("parallel", [False, True])
    def test_invalid_outer_bundle_reports_bundle_issues(
        self, tmp_path: Path, parallel: bool
    ) -> None:
        bundle = {
            "resourceType": "Bundle",
            "type": "document",
            "entry": [
                {"fullUrl": "urn:uuid:p1", "resource": _valid_patient("p1")},
                {"fullUrl": "urn:uuid:p2", "resource": _valid_patient("p2", family="Smith")},
            ],
        }
        f = tmp_path / "invalid_doc_bundle.json"
        f.write_text(json.dumps(bundle), encoding="utf-8")

        report = validate_dataset(f, parallel=parallel)
        assert report["total_resources"] == 3
        assert report["valid_resources"] == 2
        assert report["invalid_resources"] == 1
        assert any(issue.get("resourceType") == "Bundle" for issue in report["issues"])
        assert any(
            "Invariant[bdl-9]" in err
            for issue in report["issues"]
            for err in issue.get("issues", [])
        )


# ==============================================================================
# 3. Per-Bundle Symbol Table & Intra-Bundle Resolution
# ==============================================================================


class TestBundleSymbolTableAndResolution:
    def _org_profile_map(self) -> dict[str, CompiledProfile]:
        org_prof = "http://example.org/StructureDefinition/strict-org"
        pat_prof = "http://example.org/StructureDefinition/pat-with-strict-org"
        return compile_profiles(
            {
                org_prof: {
                    "base_type": "Organization",
                    "required": ["Organization.name"],
                },
                pat_prof: {
                    "base_type": "Patient",
                    "target_profiles": {"Patient.managingOrganization": [org_prof]},
                },
            }
        )

    @pytest.mark.parametrize(
        ("full_url", "ref_str"),
        [
            (
                "urn:uuid:11111111-1111-1111-1111-111111111111",
                "urn:uuid:11111111-1111-1111-1111-111111111111",
            ),
            ("urn:oid:1.2.3.4.5", "urn:oid:1.2.3.4.5"),
            ("https://example.org/fhir/Organization/org-1", "Organization/org-1"),
            (
                "https://example.org/fhir/Organization/org-1",
                "https://other.org/fhir/Organization/org-1",
            ),
        ],
    )
    def test_symbol_table_resolution_forms(self, full_url: str, ref_str: str) -> None:
        profiles = self._org_profile_map()
        pat_prof = "http://example.org/StructureDefinition/pat-with-strict-org"

        valid_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:pat-1",
                    "resource": _valid_patient(
                        managing_org={"reference": ref_str},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": full_url,
                    "resource": {"resourceType": "Organization", "id": "org-1", "name": "Acme"},
                },
            ],
        }
        assert validate_resource(valid_bundle, ig_sources=profiles) == []

        invalid_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:pat-1",
                    "resource": _valid_patient(
                        managing_org={"reference": ref_str},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": full_url,
                    "resource": {"resourceType": "Organization", "id": "org-1"},
                },
            ],
        }
        issues = validate_resource(invalid_bundle, ig_sources=profiles)
        assert any("targetProfile" in i for i in issues)

    def test_contained_reference_resolution(self) -> None:
        profiles = self._org_profile_map()
        pat_prof = "http://example.org/StructureDefinition/pat-with-strict-org"

        valid_pat = _valid_patient(
            managing_org={"reference": "#org-c"},
            contained=[{"resourceType": "Organization", "id": "org-c", "name": "Contained Org"}],
            profiles=[pat_prof],
        )
        assert validate_resource(valid_pat, ig_sources=profiles) == []

        invalid_pat = _valid_patient(
            managing_org={"reference": "#org-c"},
            contained=[{"resourceType": "Organization", "id": "org-c"}],
            profiles=[pat_prof],
        )
        issues = validate_resource(invalid_pat, ig_sources=profiles)
        assert any("targetProfile" in i for i in issues)

    def test_intra_bundle_resolution_in_validate_dataset(self, tmp_path: Path) -> None:
        pkg_dir = _make_sd_package(
            tmp_path,
            [
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/StructureDefinition/strict-org",
                    "name": "StrictOrg",
                    "status": "active",
                    "kind": "resource",
                    "type": "Organization",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Organization",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {"id": "Organization.name", "path": "Organization.name", "min": 1}
                        ]
                    },
                },
                {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/StructureDefinition/pat-strict-org",
                    "name": "PatStrictOrg",
                    "status": "active",
                    "kind": "resource",
                    "type": "Patient",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {
                                "id": "Patient.managingOrganization",
                                "path": "Patient.managingOrganization",
                                "type": [
                                    {
                                        "code": "Reference",
                                        "targetProfile": [
                                            "http://example.org/StructureDefinition/strict-org"
                                        ],
                                    }
                                ],
                            }
                        ]
                    },
                },
            ],
        )

        pat_prof = "http://example.org/StructureDefinition/pat-strict-org"
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:pat-1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:org-1"},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:org-1",
                    "resource": {"resourceType": "Organization", "id": "org-1"},
                },
            ],
        }
        bundle_file = tmp_path / "bundle.json"
        bundle_file.write_text(json.dumps(bundle), encoding="utf-8")

        report = validate_dataset(bundle_file, ig_sources=[pkg_dir])
        assert report["total_resources"] == 2
        assert report["invalid_resources"] == 1
        assert any(
            "targetProfile" in err for issue in report["issues"] for err in issue.get("issues", [])
        )


# ==============================================================================
# 4. Reference.type, targetProfile OR-semantics, Cycle Guard, & Aggregation
# ==============================================================================


class TestTargetProfilesAndAggregations:
    def test_reference_type_mismatch(self) -> None:
        prof_url = "http://example.org/StructureDefinition/pat-org-only"
        profiles = _compile_one(
            prof_url,
            {
                "base_type": "Patient",
                "target_types": {"Patient.managingOrganization": ["Organization"]},
            },
        )
        bad_explicit_type = _valid_patient(
            managing_org={"reference": "Organization/1", "type": "Location"},
            profiles=[prof_url],
        )
        issues = validate_resource(bad_explicit_type, ig_sources=profiles)
        assert any("Reference.type 'Location'" in i for i in issues)

        bad_ref_type = _valid_patient(
            managing_org={"reference": "Practitioner/1"},
            profiles=[prof_url],
        )
        issues2 = validate_resource(bad_ref_type, ig_sources=profiles)
        assert any("reference target 'Practitioner'" in i for i in issues2)

    def test_target_profile_or_semantics(self) -> None:
        org_a = "http://example.org/StructureDefinition/org-a"
        org_b = "http://example.org/StructureDefinition/org-b"
        pat_prof = "http://example.org/StructureDefinition/pat-or"
        profiles = compile_profiles(
            {
                org_a: {"base_type": "Organization", "required": ["Organization.name"]},
                org_b: {"base_type": "Organization", "required": ["Organization.telecom"]},
                pat_prof: {
                    "base_type": "Patient",
                    "target_profiles": {"Patient.managingOrganization": [org_a, org_b]},
                },
            }
        )

        # Matches org_b (has telecom, no name) -> passes OR-semantics
        bundle_ok = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:o1"},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:o1",
                    "resource": {
                        "resourceType": "Organization",
                        "id": "o1",
                        "telecom": [{"system": "phone", "value": "555-0100"}],
                    },
                },
            ],
        }
        assert validate_resource(bundle_ok, ig_sources=profiles) == []

        # Matches neither -> fails
        bundle_fail = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:o1"},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:o1",
                    "resource": {"resourceType": "Organization", "id": "o1"},
                },
            ],
        }
        issues = validate_resource(bundle_fail, ig_sources=profiles)
        assert any("does not conform to any targetProfile" in i for i in issues)

    def test_circular_reference_cycle_guard(self) -> None:
        org_prof = "http://example.org/StructureDefinition/cyclic-org"
        pat_prof = "http://example.org/StructureDefinition/pat-cyclic-org"
        profiles = compile_profiles(
            {
                org_prof: {
                    "base_type": "Organization",
                    "required": ["Organization.name"],
                    "target_profiles": {"Organization.partOf": [org_prof]},
                },
                pat_prof: {
                    "base_type": "Patient",
                    "target_profiles": {"Patient.managingOrganization": [org_prof]},
                },
            }
        )

        # Patient -> Organization -> Organization (self-cycle)
        bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:o1"},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:o1",
                    "resource": {
                        "resourceType": "Organization",
                        "id": "o1",
                        "name": "Cyclic Org",
                        "partOf": {"reference": "urn:uuid:o1"},
                    },
                },
            ],
        }
        assert validate_resource(bundle, ig_sources=profiles) == []

    def test_target_aggregation_modes(self) -> None:
        contained_prof = "http://example.org/StructureDefinition/pat-agg-contained"
        referenced_prof = "http://example.org/StructureDefinition/pat-agg-referenced"
        bundled_prof = "http://example.org/StructureDefinition/pat-agg-bundled"
        profiles = compile_profiles(
            {
                contained_prof: {
                    "base_type": "Patient",
                    "target_aggregations": {"Patient.managingOrganization": ["contained"]},
                },
                referenced_prof: {
                    "base_type": "Patient",
                    "target_aggregations": {"Patient.managingOrganization": ["referenced"]},
                },
                bundled_prof: {
                    "base_type": "Patient",
                    "target_aggregations": {"Patient.managingOrganization": ["bundled"]},
                },
            }
        )

        # contained: #org ok, Organization/1 fails
        assert (
            validate_resource(
                _valid_patient(
                    managing_org={"reference": "#org-1"},
                    contained=[{"resourceType": "Organization", "id": "org-1"}],
                    profiles=[contained_prof],
                ),
                ig_sources=profiles,
            )
            == []
        )
        issues_c = validate_resource(
            _valid_patient(
                managing_org={"reference": "Organization/1"},
                profiles=[contained_prof],
            ),
            ig_sources=profiles,
        )
        assert any("must be contained" in i for i in issues_c)

        # referenced: Organization/1 ok, #org fails
        assert (
            validate_resource(
                _valid_patient(
                    managing_org={"reference": "Organization/1"},
                    profiles=[referenced_prof],
                ),
                ig_sources=profiles,
            )
            == []
        )
        issues_r = validate_resource(
            _valid_patient(
                managing_org={"reference": "#org-1"},
                contained=[{"resourceType": "Organization", "id": "org-1"}],
                profiles=[referenced_prof],
            ),
            ig_sources=profiles,
        )
        assert any("'contained' aggregation" in i for i in issues_r)

        # bundled: resolves in Bundle ok, missing from Bundle fails
        bundled_ok = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:o1"},
                        profiles=[bundled_prof],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:o1",
                    "resource": {"resourceType": "Organization", "id": "o1"},
                },
            ],
        }
        assert validate_resource(bundled_ok, ig_sources=profiles) == []

        bundled_fail = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "Organization/missing"},
                        profiles=[bundled_prof],
                    ),
                },
            ],
        }
        issues_b = validate_resource(bundled_fail, ig_sources=profiles)
        assert any("('bundled' aggregation)" in i for i in issues_b)

    def test_runtime_ig_preserves_target_profiles_and_aggregations(self, tmp_path: Path) -> None:
        sd_url = "http://example.org/StructureDefinition/pat-runtime-ref"
        tp_url = "http://hl7.org/fhir/StructureDefinition/Organization"
        pkg_dir = _make_sd_package(
            tmp_path,
            [
                {
                    "resourceType": "StructureDefinition",
                    "url": sd_url,
                    "name": "PatRuntimeRef",
                    "status": "active",
                    "kind": "resource",
                    "type": "Patient",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {
                                "id": "Patient.managingOrganization",
                                "path": "Patient.managingOrganization",
                                "type": [
                                    {
                                        "code": "Reference",
                                        "targetProfile": [tp_url],
                                        "aggregation": ["contained"],
                                    }
                                ],
                            }
                        ]
                    },
                }
            ],
        )

        prof_map, _ = load_compiled_ig_bundle([pkg_dir])
        compiled = prof_map[sd_url]
        assert any(
            r.path == "Patient.managingOrganization" and tp_url in r.allowed
            for r in compiled.target_profiles
        )
        assert any(
            r.path == "Patient.managingOrganization" and "contained" in r.allowed
            for r in compiled.target_aggregations
        )

        # Runtime validation enforces both targetProfile and aggregation
        issues = validate_resource(
            _valid_patient(
                managing_org={"reference": "Organization/1"},
                profiles=[sd_url],
            ),
            ig_sources=[pkg_dir],
        )
        assert any("must be contained" in i for i in issues)

    def test_validate_dataset_bundle_ignores_non_bundle_profile_urls(self, tmp_path: Path) -> None:
        us_core_patient = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
        valid_us_core_patient = {
            "resourceType": "Patient",
            "id": "pat-1",
            "identifier": [{"system": "http://example.org/mrn", "value": "12345"}],
            "name": [{"family": "Doe", "given": ["Jane"]}],
            "gender": "female",
        }
        bundle_ok = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"fullUrl": "urn:uuid:pat-1", "resource": valid_us_core_patient}],
        }
        ok_path = tmp_path / "ok_bundle.json"
        ok_path.write_text(json.dumps(bundle_ok), encoding="utf-8")

        report_ok = validate_dataset(ok_path, profile_urls=[us_core_patient])
        assert report_ok["valid_resources"] == 1
        assert report_ok["invalid_resources"] == 0
        assert report_ok["issues"] == []

        # Inner Patient missing required US Core fields fails, but outer Bundle does not
        # spuriously fail "profile applies to 'Patient', got 'Bundle'".
        bundle_bad = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"fullUrl": "urn:uuid:pat-1", "resource": _valid_patient()}],
        }
        bad_path = tmp_path / "bad_bundle.json"
        bad_path.write_text(json.dumps(bundle_bad), encoding="utf-8")

        report_bad = validate_dataset(bad_path, profile_urls=[us_core_patient])
        assert report_bad["valid_resources"] == 0
        assert report_bad["invalid_resources"] == 1
        all_msgs = [msg for entry in report_bad["issues"] for msg in entry.get("issues", [])]
        assert not any("profile applies to 'Patient', got 'Bundle'" in m for m in all_msgs)
        assert any("Profile[" in m for m in all_msgs)

    def test_versioned_target_profile_stripped_and_normalized(self, tmp_path: Path) -> None:
        org_url = "http://example.org/StructureDefinition/ver-org"
        pat_url = "http://example.org/StructureDefinition/ver-pat"
        pkg_dir = _make_sd_package(
            tmp_path,
            [
                {
                    "resourceType": "StructureDefinition",
                    "url": org_url,
                    "name": "VerOrg",
                    "status": "active",
                    "kind": "resource",
                    "type": "Organization",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Organization",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {"id": "Organization.name", "path": "Organization.name", "min": 1}
                        ]
                    },
                },
                {
                    "resourceType": "StructureDefinition",
                    "url": pat_url,
                    "name": "VerPat",
                    "status": "active",
                    "kind": "resource",
                    "type": "Patient",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {
                                "id": "Patient.managingOrganization",
                                "path": "Patient.managingOrganization",
                                "type": [
                                    {
                                        "code": "Reference",
                                        "targetProfile": [f"{org_url}|6.1.0"],
                                    }
                                ],
                            }
                        ]
                    },
                },
            ],
        )

        prof_map, _ = load_compiled_ig_bundle([pkg_dir])
        compiled_pat = prof_map[pat_url]
        assert any(
            r.path == "Patient.managingOrganization" and r.allowed == frozenset({org_url})
            for r in compiled_pat.target_profiles
        )

        # Also verify _target_conforms_to_profile normalizes versioned tp_url directly
        direct_profiles = compile_profiles(
            {
                org_url: {"base_type": "Organization", "required": ["Organization.name"]},
                pat_url: {
                    "base_type": "Patient",
                    "target_profiles": {"Patient.managingOrganization": [f"{org_url}|4.0.1"]},
                },
            }
        )
        bundle_fail = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:o1"},
                        profiles=[pat_url],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:o1",
                    "resource": {"resourceType": "Organization", "id": "o1"},
                },
            ],
        }
        issues = validate_resource(bundle_fail, ig_sources=direct_profiles)
        assert any("does not conform to any targetProfile" in i for i in issues)

    def test_base_profile_fallback_checks_resource_type(self) -> None:
        pat_prof = "http://example.org/StructureDefinition/pat-org-target"
        base_org = "http://hl7.org/fhir/StructureDefinition/Organization"
        profiles = compile_profiles(
            {
                pat_prof: {
                    "base_type": "Patient",
                    "target_profiles": {"Patient.managingOrganization": [base_org]},
                }
            }
        )

        # Wrong resourceType -> fails
        wrong_rt_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:p1",
                    "resource": _valid_patient(
                        managing_org={"reference": "urn:uuid:loc-1"},
                        profiles=[pat_prof],
                    ),
                },
                {
                    "fullUrl": "urn:uuid:loc-1",
                    "resource": {"resourceType": "Location", "id": "loc-1"},
                },
            ],
        }
        issues_wrong = validate_resource(wrong_rt_bundle, ig_sources=profiles)
        assert any("does not conform to any targetProfile" in i for i in issues_wrong)

        # Missing resourceType in contained target -> fails
        missing_rt_patient = _valid_patient(
            managing_org={"reference": "#bad-1"},
            contained=[{"id": "bad-1"}],
            profiles=[pat_prof],
        )
        issues_missing = validate_resource(missing_rt_patient, ig_sources=profiles)
        assert any("does not conform to any targetProfile" in i for i in issues_missing)

    def test_nested_bundle_merges_outer_and_inner_indices(self) -> None:
        org_prof = "http://example.org/StructureDefinition/nested-org"
        pat_prof = "http://example.org/StructureDefinition/nested-pat"
        profiles = compile_profiles(
            {
                org_prof: {"base_type": "Organization", "required": ["Organization.name"]},
                pat_prof: {
                    "base_type": "Patient",
                    "target_profiles": {"Patient.managingOrganization": [org_prof]},
                },
            }
        )

        # Outer Bundle provides org-outer; inner Bundle has Patient referencing urn:uuid:org-outer
        outer_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "urn:uuid:org-outer",
                    "resource": {"resourceType": "Organization", "id": "org-outer"},
                },
                {
                    "fullUrl": "urn:uuid:inner-bdl",
                    "resource": {
                        "resourceType": "Bundle",
                        "type": "collection",
                        "entry": [
                            {
                                "fullUrl": "urn:uuid:p1",
                                "resource": _valid_patient(
                                    managing_org={"reference": "urn:uuid:org-outer"},
                                    profiles=[pat_prof],
                                ),
                            }
                        ],
                    },
                },
            ],
        }
        issues = validate_resource(outer_bundle, ig_sources=profiles)
        assert any("does not conform to any targetProfile" in i for i in issues)
