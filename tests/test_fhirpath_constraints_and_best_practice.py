"""Tests for AOT + runtime FHIRPath constraints and --best-practice warnings."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fhirlance.cli import main as cli_main
from fhirlance.dataset import validate_dataset
from fhirlance.ig_loader import load_compiled_ig_profiles
from fhirlance.resource_validator import validate_resource


def _valid_patient(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "resourceType": "Patient",
        "id": "pat-1",
        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Pat</div>",
        },
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
    }
    base.update(overrides)
    return base


class TestBaseR4Constraints:
    def test_dom2_nested_contained_rejected(self) -> None:
        pat = _valid_patient(
            generalPractitioner=[{"reference": "#c1"}],
            contained=[
                {
                    "resourceType": "Practitioner",
                    "id": "c1",
                    "contained": [{"resourceType": "Organization", "id": "c2", "name": "Nested"}],
                }
            ],
        )
        issues = validate_resource(pat)
        assert any("Invariant[dom-2]" in i for i in issues)

    def test_dom3_unreferenced_contained_rejected_and_referenced_passes(self) -> None:
        unreferenced = _valid_patient(
            contained=[{"resourceType": "Organization", "id": "org-1", "name": "Orphan"}]
        )
        issues_bad = validate_resource(unreferenced)
        assert any("Invariant[dom-3]" in i for i in issues_bad)

        referenced = _valid_patient(
            managingOrganization={"reference": "#org-1"},
            contained=[{"resourceType": "Organization", "id": "org-1", "name": "Linked"}],
        )
        assert validate_resource(referenced) == []

    def test_dom4_contained_meta_version_and_last_updated_rejected(self) -> None:
        pat = _valid_patient(
            managingOrganization={"reference": "#org-1"},
            contained=[
                {
                    "resourceType": "Organization",
                    "id": "org-1",
                    "name": "Org",
                    "meta": {"versionId": "1"},
                }
            ],
        )
        issues = validate_resource(pat)
        assert any("Invariant[dom-4]" in i for i in issues)

    def test_dom5_contained_meta_security_rejected(self) -> None:
        pat = _valid_patient(
            managingOrganization={"reference": "#org-1"},
            contained=[
                {
                    "resourceType": "Organization",
                    "id": "org-1",
                    "name": "Org",
                    "meta": {
                        "security": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/v3-Confidentiality",
                                "code": "R",
                            }
                        ]
                    },
                }
            ],
        )
        issues = validate_resource(pat)
        assert any("Invariant[dom-5]" in i for i in issues)

    def test_obs3_reference_range_requires_low_high_or_text(self) -> None:
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "1234-5"}]},
            "referenceRange": [{}],
        }
        issues = validate_resource(obs)
        assert any("Invariant[obs-3]" in i for i in issues)


class TestBuiltinIGProfileConstraints:
    def test_us_core_practitioner_npi_constraints(self) -> None:
        prof = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"
        # Valid 10-digit Luhn NPI: 1234567893
        valid_pract = {
            "resourceType": "Practitioner",
            "meta": {"profile": [prof]},
            "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567893"}],
            "name": [{"family": "Smith", "given": ["Alice"]}],
        }
        assert validate_resource(valid_pract) == []

        # Bad Luhn check digit (fails us-core-17)
        bad_luhn = {
            **valid_pract,
            "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567890"}],
        }
        issues_luhn = validate_resource(bad_luhn)
        assert any("Invariant[us-core-17]" in i for i in issues_luhn)

        # Non-10-digit NPI (fails us-core-16)
        bad_len = {
            **valid_pract,
            "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "12345"}],
        }
        issues_len = validate_resource(bad_len)
        assert any("Invariant[us-core-16]" in i for i in issues_len)

    def test_us_core_patient_name_constraint(self) -> None:
        prof = "http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"
        pat = _valid_patient(
            meta={"profile": [prof]},
            identifier=[{"system": "http://example.org/mrn", "value": "123"}],
            name=[{"use": "official"}],
        )
        issues = validate_resource(pat)
        assert any("Invariant[us-core-6]" in i for i in issues)

    def test_ips_patient_constraint(self) -> None:
        prof = "http://hl7.org/fhir/uv/ips/StructureDefinition/Patient-uv-ips"
        pat = _valid_patient(
            meta={"profile": [prof]},
            name=[{"text": "Only Text"}],
        )
        issues = validate_resource(pat)
        assert any("Invariant[ips-pat-1]" in i for i in issues)


class TestRuntimeIGConstraintsAndPreferredBindings:
    def test_runtime_ig_custom_constraint_and_preferred_binding(self, tmp_path: Path) -> None:
        pkg = tmp_path / "custom-ig"
        pkg.mkdir()
        (pkg / "package.json").write_text(
            json.dumps({"name": "example.custom", "version": "1.0.0"}), encoding="utf-8"
        )
        vs = {
            "resourceType": "ValueSet",
            "url": "http://example.org/ValueSet/custom-pref",
            "status": "active",
            "compose": {
                "include": [
                    {
                        "system": "http://example.org/CodeSystem/custom",
                        "concept": [{"code": "en"}],
                    }
                ]
            },
        }
        sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/StructureDefinition/custom-patient",
            "name": "CustomPatient",
            "status": "active",
            "kind": "resource",
            "type": "Patient",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
            "derivation": "constraint",
            "differential": {
                "element": [
                    {
                        "id": "Patient",
                        "path": "Patient",
                        "constraint": [
                            {
                                "key": "cust-1",
                                "severity": "error",
                                "human": "Patient must be active",
                                "expression": "active = true",
                            },
                            {
                                "key": "cust-2",
                                "severity": "warning",
                                "human": "Patient should have birthDate",
                                "expression": "birthDate.exists()",
                            },
                        ],
                    },
                    {
                        "id": "Patient.language",
                        "path": "Patient.language",
                        "binding": {
                            "strength": "preferred",
                            "valueSet": "http://example.org/ValueSet/custom-pref",
                        },
                    },
                ]
            },
        }
        (pkg / "vs.json").write_text(json.dumps(vs), encoding="utf-8")
        (pkg / "sd.json").write_text(json.dumps(sd), encoding="utf-8")

        compiled = load_compiled_ig_profiles([pkg])
        prof_url = "http://example.org/StructureDefinition/custom-patient"

        warnings_bad: list[str] = []
        bad_pat = _valid_patient(
            meta={"profile": [prof_url]},
            active=False,
            language="bad-code",
        )
        issues = validate_resource(
            bad_pat, ig_sources=compiled, best_practice=True, _warnings_out=warnings_bad
        )
        assert any("Invariant[cust-1]" in i for i in issues)
        assert any("Warning: Invariant[cust-2]" in w for w in warnings_bad)
        assert any("preferred" in w.lower() for w in warnings_bad)

        warnings_ok: list[str] = []
        ok_pat = _valid_patient(
            meta={"profile": [prof_url]},
            active=True,
            birthDate="1990-01-01",
            language="en",
        )
        assert (
            validate_resource(
                ok_pat, ig_sources=compiled, best_practice=True, _warnings_out=warnings_ok
            )
            == []
        )
        assert warnings_ok == []


class TestBestPracticeWarnings:
    def test_best_practice_dom6_obs_performer_and_preferred_binding(self) -> None:
        # 1. DomainResource without text.div -> dom-6 warning only when best_practice=True
        pat_no_text = {"resourceType": "Patient", "id": "p1"}
        w_off: list[str] = []
        assert validate_resource(pat_no_text, _warnings_out=w_off) == []
        assert not any("dom-6" in w for w in w_off)

        w_on: list[str] = []
        assert validate_resource(pat_no_text, best_practice=True, _warnings_out=w_on) == []
        assert any("BestPractice[dom-6]" in w for w in w_on)

        # 2. Bundle / Binary / Parameters do NOT emit dom-6
        w_bundle: list[str] = []
        bundle = {"resourceType": "Bundle", "type": "collection"}
        assert validate_resource(bundle, best_practice=True, _warnings_out=w_bundle) == []
        assert not any("dom-6" in w for w in w_bundle)

        # 3. Observation without performer -> obs-performer warning; with performer -> none
        obs_no_perf = {
            "resourceType": "Observation",
            "text": {
                "status": "generated",
                "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Obs</div>",
            },
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "1234-5"}]},
        }
        w_obs: list[str] = []
        assert validate_resource(obs_no_perf, best_practice=True, _warnings_out=w_obs) == []
        assert any("BestPractice[obs-performer]" in w for w in w_obs)

        obs_with_perf = {**obs_no_perf, "performer": [{"reference": "Practitioner/1"}]}
        w_obs_ok: list[str] = []
        assert validate_resource(obs_with_perf, best_practice=True, _warnings_out=w_obs_ok) == []
        assert not any("obs-performer" in w for w in w_obs_ok)

        # 4. Base resource preferred binding (Condition.severity)
        cond_bad_sev = {
            "resourceType": "Condition",
            "text": {
                "status": "generated",
                "div": "<div xmlns='http://www.w3.org/1999/xhtml'>Cond</div>",
            },
            "subject": {"reference": "Patient/1"},
            "severity": {"coding": [{"system": "http://snomed.info/sct", "code": "not-a-sev"}]},
        }
        w_cond: list[str] = []
        assert validate_resource(cond_bad_sev, best_practice=True, _warnings_out=w_cond) == []
        assert any("Condition.severity" in w for w in w_cond)

    def test_best_practice_dataset_and_cli(self, tmp_path: Path, capsys: Any) -> None:
        obs_file = tmp_path / "obs.json"
        obs_file.write_text(
            json.dumps(
                {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {"coding": [{"system": "http://loinc.org", "code": "1234-5"}]},
                }
            ),
            encoding="utf-8",
        )

        report_off = validate_dataset(obs_file)
        assert report_off["warnings"] == []

        report_on = validate_dataset(obs_file, best_practice=True)
        assert report_on["valid_resources"] == 1
        assert len(report_on["warnings"]) == 1
        warn_msgs = report_on["warnings"][0]["warnings"]
        assert any("BestPractice[dom-6]" in w for w in warn_msgs)
        assert any("BestPractice[obs-performer]" in w for w in warn_msgs)

        exit_code = cli_main([str(obs_file), "--best-practice", "--json"])
        assert exit_code == 0
        out = json.loads(capsys.readouterr().out)
        assert len(out["warnings"]) == 1
