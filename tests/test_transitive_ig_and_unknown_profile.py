"""Tests for transitive IG package resolution, runtime VS expansion, and unknown_profile."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from fhirlance.cli import main as cli_main
from fhirlance.dataset import validate_dataset
from fhirlance.ig_loader import clear_ig_cache, load_compiled_ig_bundle
from fhirlance.profile_engine import COMPILED_PROFILES, validate_single_profile
from fhirlance.profiles import COMPLETE_CODE_SYSTEMS, VALUE_SET_SPECS
from fhirlance.resource_validator import validate_resource
from fhirlance.terminology import TxOptions, validate_binding_value, validate_standalone_codings


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def _patient_profile(
    url: str,
    *,
    base_def: str = "http://hl7.org/fhir/StructureDefinition/Patient",
    elements: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "resourceType": "StructureDefinition",
        "url": url,
        "name": url.rsplit("/", 1)[-1],
        "status": "active",
        "kind": "resource",
        "abstract": False,
        "type": "Patient",
        "baseDefinition": base_def,
        "derivation": "constraint",
        "differential": {
            "element": [{"id": "Patient", "path": "Patient"}, *(elements or [])],
        },
    }


@pytest.fixture(autouse=True)
def _reset_ig_cache() -> Any:
    clear_ig_cache()
    yield
    clear_ig_cache()


def test_transitive_package_dependency_resolution(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cache_dir = tmp_path / "cache"
    monkeypatch.setenv("FHIRLANCE_CACHE_DIR", str(cache_dir))

    dep_pkg = cache_dir / "packages" / "dep.ig#1.0.0" / "package"
    _write_json(
        dep_pkg / "package.json",
        {
            "name": "dep.ig",
            "version": "1.0.0",
            "dependencies": {"hl7.fhir.r4.core": "4.0.1"},
        },
    )
    dep_url = "http://example.org/StructureDefinition/dep-patient"
    _write_json(
        dep_pkg / "StructureDefinition-dep-patient.json",
        _patient_profile(
            dep_url,
            elements=[{"id": "Patient.birthDate", "path": "Patient.birthDate", "min": 1}],
        ),
    )

    root_ig = tmp_path / "root_ig"
    _write_json(
        root_ig / "package.json",
        {
            "name": "root.ig",
            "version": "1.0.0",
            "dependencies": {
                "dep.ig": "1.0.0",
                "hl7.fhir.r4.core": "4.0.1",
                "hl7.fhir.r4.examples": "4.0.1",
            },
        },
    )
    root_url = "http://example.org/StructureDefinition/root-patient"
    _write_json(
        root_ig / "StructureDefinition-root-patient.json",
        _patient_profile(
            root_url,
            base_def=dep_url,
            elements=[{"id": "Patient.gender", "path": "Patient.gender", "min": 1}],
        ),
    )

    profiles, _ = load_compiled_ig_bundle([root_ig])
    assert dep_url in profiles
    assert root_url in profiles

    issues = validate_resource(
        {"resourceType": "Patient", "meta": {"profile": [root_url]}},
        ig_sources=[root_ig],
        tx="off",
    )
    assert any("birthDate" in i for i in issues)
    assert any("gender" in i for i in issues)


def test_runtime_ig_supplements_filters_exclude_and_versioned_vs(tmp_path: Path) -> None:
    ig_dir = tmp_path / "term_ig"
    cs_url = "http://example.org/cs/org"
    _write_json(
        ig_dir / "CodeSystem-org.json",
        {
            "resourceType": "CodeSystem",
            "url": cs_url,
            "version": "1.0.0",
            "status": "active",
            "content": "complete",
            "concept": [
                {
                    "code": "root",
                    "concept": [
                        {
                            "code": "branch",
                            "concept": [{"code": "leaf1"}, {"code": "leaf2"}],
                        },
                        {"code": "sibling"},
                    ],
                }
            ],
        },
    )
    _write_json(
        ig_dir / "CodeSystem-org-sup.json",
        {
            "resourceType": "CodeSystem",
            "url": "http://example.org/cs/org-sup",
            "status": "active",
            "content": "supplement",
            "supplements": f"{cs_url}|1.0.0",
            "concept": [
                {
                    "code": "leaf1",
                    "property": [{"code": "active_flag", "valueBoolean": True}],
                }
            ],
        },
    )
    _write_json(
        ig_dir / "ValueSet-children.json",
        {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/children",
            "version": "1.0.0",
            "status": "active",
            "compose": {
                "include": [
                    {
                        "system": cs_url,
                        "filter": [{"property": "concept", "op": "child-of", "value": "root"}],
                    }
                ],
                "exclude": [{"system": cs_url, "concept": [{"code": "sibling"}]}],
            },
        },
    )
    _write_json(
        ig_dir / "ValueSet-generalizes.json",
        {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/generalizes",
            "version": "1.0.0",
            "status": "active",
            "compose": {
                "include": [
                    {
                        "system": cs_url,
                        "filter": [{"property": "concept", "op": "generalizes", "value": "leaf1"}],
                    }
                ]
            },
        },
    )
    _write_json(
        ig_dir / "ValueSet-sup-exists.json",
        {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/sup-exists",
            "version": "1.0.0",
            "status": "active",
            "compose": {
                "include": [
                    {
                        "system": cs_url,
                        "filter": [{"property": "active_flag", "op": "exists", "value": "true"}],
                    }
                ]
            },
        },
    )
    _write_json(
        ig_dir / "ValueSet-ver-1.json",
        {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/ver",
            "version": "1.0.0",
            "status": "active",
            "compose": {"include": [{"system": cs_url, "concept": [{"code": "leaf1"}]}]},
        },
    )
    _write_json(
        ig_dir / "ValueSet-ver-2.json",
        {
            "resourceType": "ValueSet",
            "url": "http://example.org/vs/ver",
            "version": "2.0.0",
            "status": "active",
            "compose": {"include": [{"system": cs_url, "concept": [{"code": "leaf2"}]}]},
        },
    )

    p_children = "http://example.org/StructureDefinition/p-children"
    p_gen = "http://example.org/StructureDefinition/p-gen"
    p_sup = "http://example.org/StructureDefinition/p-sup"
    p_ver = "http://example.org/StructureDefinition/p-ver"
    for p_url, vs_ref in (
        (p_children, "http://example.org/vs/children|1.0.0"),
        (p_gen, "http://example.org/vs/generalizes|1.0.0"),
        (p_sup, "http://example.org/vs/sup-exists|1.0.0"),
        (p_ver, "http://example.org/vs/ver|1.0.0"),
    ):
        _write_json(
            ig_dir / f"StructureDefinition-{p_url.rsplit('/', 1)[-1]}.json",
            _patient_profile(
                p_url,
                elements=[
                    {
                        "id": "Patient.maritalStatus",
                        "path": "Patient.maritalStatus",
                        "binding": {"strength": "required", "valueSet": vs_ref},
                    }
                ],
            ),
        )

    def _patient(code: str, prof: str) -> dict[str, Any]:
        return {
            "resourceType": "Patient",
            "meta": {"profile": [prof]},
            "maritalStatus": {"coding": [{"system": cs_url, "code": code}]},
        }

    assert validate_resource(_patient("branch", p_children), ig_sources=[ig_dir]) == []
    assert validate_resource(_patient("sibling", p_children), ig_sources=[ig_dir]) != []

    assert validate_resource(_patient("root", p_gen), ig_sources=[ig_dir]) == []
    assert validate_resource(_patient("leaf2", p_gen), ig_sources=[ig_dir]) != []

    assert validate_resource(_patient("leaf1", p_sup), ig_sources=[ig_dir]) == []
    assert validate_resource(_patient("leaf2", p_sup), ig_sources=[ig_dir]) != []

    assert validate_resource(_patient("leaf1", p_ver), ig_sources=[ig_dir]) == []
    assert validate_resource(_patient("leaf2", p_ver), ig_sources=[ig_dir]) != []


def test_versioned_builtin_terminology_lookup() -> None:
    opts = TxOptions(mode="local")
    # Pick a versioned ValueSet from VALUE_SET_SPECS and verify exact + fallback lookup
    versioned_vs = next(k for k in VALUE_SET_SPECS if "|" in k)
    base_vs = versioned_vs.split("|", 1)[0]
    sample_code = next(iter(VALUE_SET_SPECS[versioned_vs]["codes"]))

    res_exact = validate_binding_value(sample_code, "Test.code", versioned_vs, "required", opts)
    assert res_exact.errors == []

    res_fallback = validate_binding_value(
        sample_code, "Test.code", f"{base_vs}|999.0.0", "required", opts
    )
    assert res_fallback.errors == []

    res_bad = validate_binding_value(
        "__not_a_valid_code__", "Test.code", versioned_vs, "required", opts
    )
    assert len(res_bad.errors) == 1

    # Complete CodeSystem versioned + fallback lookup in standalone coding scan
    cs_url = next(k for k in COMPLETE_CODE_SYSTEMS if "|" not in k and COMPLETE_CODE_SYSTEMS[k])
    valid_cs_code = COMPLETE_CODE_SYSTEMS[cs_url][0]
    coding_ok = {
        "resourceType": "Patient",
        "maritalStatus": {"coding": [{"system": f"{cs_url}|4.0.1", "code": valid_cs_code}]},
    }
    coding_bad = {
        "resourceType": "Patient",
        "maritalStatus": {"coding": [{"system": f"{cs_url}|99.0.0", "code": "__bad__"}]},
    }
    assert (
        validate_standalone_codings(coding_ok, opts, complete_systems=COMPLETE_CODE_SYSTEMS).errors
        == []
    )
    assert (
        len(
            validate_standalone_codings(
                coding_bad, opts, complete_systems=COMPLETE_CODE_SYSTEMS
            ).errors
        )
        == 1
    )


def test_unknown_profile_modes_across_engines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    unknown_url = "http://example.org/StructureDefinition/unknown-profile"
    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": "p1",
        "meta": {"profile": [unknown_url]},
    }

    # 1. validate_single_profile
    assert validate_single_profile(patient, "Patient", unknown_url) == []
    warnings: list[str] = []
    assert (
        validate_single_profile(
            patient, "Patient", unknown_url, unknown_profile="warning", _warnings_out=warnings
        )
        == []
    )
    assert warnings == [f"Profile[{unknown_url}]: unknown profile '{unknown_url}'"]
    assert validate_single_profile(patient, "Patient", unknown_url, unknown_profile="error") == [
        f"Profile[{unknown_url}]: unknown profile '{unknown_url}'"
    ]
    # Known profile with |version falls back to versionless key
    known_patient_prof = next(
        k
        for k, v in COMPILED_PROFILES.items()
        if "|" not in k and v.base_type == "Patient" and not v.required
    )
    assert (
        validate_single_profile(
            patient,
            "Patient",
            f"{known_patient_prof}|99.0.0",
            unknown_profile="error",
        )
        == []
    )

    # 2. validate_resource (including nested Bundle entry)
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [{"resource": patient}],
    }
    assert validate_resource(bundle, unknown_profile="ignore") == []
    res_warns: list[str] = []
    assert validate_resource(bundle, unknown_profile="warning", _warnings_out=res_warns) == []
    assert any(unknown_url in w for w in res_warns)
    res_errs = validate_resource(bundle, unknown_profile="error")
    assert any(unknown_url in e for e in res_errs)

    # 3. validate_dataset (sequential & parallel)
    p_file = tmp_path / "patient.json"
    _write_json(p_file, patient)
    rep_ign = validate_dataset(p_file, unknown_profile="ignore")
    assert rep_ign["invalid_resources"] == 0
    assert rep_ign["warnings"] == []

    rep_warn = validate_dataset(p_file, unknown_profile="warning")
    assert rep_warn["invalid_resources"] == 0
    assert len(rep_warn["warnings"]) == 1

    rep_err = validate_dataset(p_file, unknown_profile="error")
    assert rep_err["invalid_resources"] == 1
    assert any(unknown_url in str(rep_err["issues"]) for _ in [0])

    # 4. cli.main
    assert cli_main([str(p_file), "--unknown-profile", "ignore", "--format", "json"]) == 0
    capsys.readouterr()
    assert cli_main([str(p_file), "--unknown-profile", "warning", "--format", "json"]) == 0
    out_warn = json.loads(capsys.readouterr().out)
    assert len(out_warn["warnings"]) == 1
    assert cli_main([str(p_file), "--unknown-profile", "error", "--format", "json"]) == 1
    out_err = json.loads(capsys.readouterr().out)
    assert out_err["invalid_resources"] == 1
