"""Targeted edge-case and coverage-gap tests for Tier 2 and extension/IG engines."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from fhirlance.base import check_value_bounds
from fhirlance.cli import main as cli_main
from fhirlance.extension_spec import extract_extension_spec
from fhirlance.ig_loader import load_compiled_ig_bundle
from fhirlance.resource_validator import _resolve_questionnaire, validate_resource


def test_extension_spec_bindings_targets_snapshot_and_star_max() -> None:
    """extract_extension_spec handles bindings, targetProfile fallbacks, snapshot, and max='*'."""
    ext_url = "http://example.org/StructureDefinition/ext-bound"
    sd: dict[str, Any] = {
        "resourceType": "StructureDefinition",
        "url": f"{ext_url}|1.0.0",
        "name": "ExtBound",
        "status": "active",
        "kind": "complex-type",
        "abstract": False,
        "type": "Extension",
        "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
        "derivation": "constraint",
        "context": [{"type": "element", "expression": "Patient"}],
        "snapshot": {
            "element": [
                {"id": "NonExtension.id", "path": "NonExtension.id"},
                {
                    "id": "Extension.extension:sub",
                    "path": "Extension.extension",
                    "sliceName": "sub",
                    "min": 0,
                    "max": "*",
                },
            ]
        },
        "differential": {
            "element": [
                {
                    "id": "Extension.extension:sub.url",
                    "path": "Extension.extension.url",
                    "fixedUri": "sub",
                },
                {
                    "id": "Extension.extension:sub.value[x]",
                    "path": "Extension.extension.value[x]",
                    "type": [{"code": "code"}],
                    "binding": {
                        "strength": "extensible",
                        "valueSet": "http://example.org/ValueSet/colors|1.0.0",
                    },
                },
                {
                    "id": "Extension.value[x]",
                    "path": "Extension.value[x]",
                    "type": [{"code": "Reference", "targetProfile": "not-a-list"}],
                    "binding": {
                        "strength": "example",
                        "valueSet": "http://example.org/ValueSet/ignored",
                    },
                },
            ]
        },
    }
    vs_specs = {
        "http://example.org/ValueSet/colors": {
            "codes": ["red", "blue"],
            "system_codes": {},
            "external_systems": [],
        }
    }
    raw = extract_extension_spec(sd, {}, {}, vs_specs=vs_specs)
    assert raw["url"] == ext_url
    sub = raw["node"]["sub_extensions"]["sub"]
    assert sub["max"] is None
    assert sub["value_binding"]["strength"] == "extensible"
    assert sub["value_binding"]["vs_spec"]["codes"] == ["red", "blue"]
    assert raw["node"]["value_binding"] is None

    # Also test targetProfile slug fallback without sd_type_by_url
    sd_ref = {
        "resourceType": "StructureDefinition",
        "url": "http://example.org/StructureDefinition/ext-ref",
        "type": "Extension",
        "differential": {
            "element": [
                {
                    "id": "Extension.value[x]",
                    "path": "Extension.value[x]",
                    "type": [
                        {
                            "code": "Reference",
                            "targetProfile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
                        }
                    ],
                }
            ]
        },
    }
    raw_ref = extract_extension_spec(sd_ref, {}, {})
    assert raw_ref["node"]["value_target_types"] == ["Patient"]


def test_extensions_fhirpath_context_prim_value_and_binding_warnings(tmp_path: Path) -> None:
    """Test fhirpath context, _value[x] required type check, and extensible binding warnings."""
    ext_url = "http://example.org/StructureDefinition/ext-fp-bound"
    vs_url = "http://example.org/ValueSet/ext-warn-vs"
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "CodeSystem",
                    "url": "http://example.org/CodeSystem/ext-cs",
                    "status": "active",
                    "content": "complete",
                    "concept": [{"code": "known"}],
                }
            },
            {
                "resource": {
                    "resourceType": "ValueSet",
                    "url": vs_url,
                    "status": "active",
                    "compose": {"include": [{"system": "http://example.org/CodeSystem/ext-cs"}]},
                }
            },
            {
                "resource": {
                    "resourceType": "StructureDefinition",
                    "url": ext_url,
                    "name": "ExtFpBound",
                    "status": "active",
                    "kind": "complex-type",
                    "abstract": False,
                    "type": "Extension",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Extension",
                    "derivation": "constraint",
                    "context": [
                        {"type": "fhirpath", "expression": "Patient"},
                        {"type": "fhirpath", "expression": "Observation.where(status='final')"},
                    ],
                    "differential": {
                        "element": [
                            {"id": "Extension.value[x]", "path": "Extension.value[x]", "min": 1},
                            {
                                "id": "Extension.value[x]",
                                "path": "Extension.value[x]",
                                "type": [{"code": "Coding"}],
                                "binding": {"strength": "extensible", "valueSet": vs_url},
                            },
                        ]
                    },
                }
            },
        ],
    }
    ig_file = tmp_path / "ig.json"
    ig_file.write_text(__import__("json").dumps(bundle), encoding="utf-8")

    # 1. Extensible binding warning on external system (not in known complete CS)
    warnings: list[str] = []
    pat = {
        "resourceType": "Patient",
        "extension": [
            {
                "url": ext_url,
                "valueCoding": {
                    "system": "http://snomed.info/sct",
                    "code": "123456",
                },
            }
        ],
    }
    issues = validate_resource(pat, ig_sources=[ig_file], tx="local", _warnings_out=warnings)
    assert issues == []
    assert any("snomed.info/sct" in w or vs_url in w for w in warnings)

    # 2. _valueString primitive-only extension fails allowed_value_keys (expects Coding)
    pat_bad_prim = {
        "resourceType": "Patient",
        "extension": [
            {
                "url": ext_url,
                "_valueString": {
                    "extension": [{"url": "http://example.org/sub", "valueBoolean": True}]
                },
            }
        ],
    }
    issues_prim = validate_resource(pat_bad_prim, ig_sources=[ig_file], tx="off")
    assert any("requires value[x] type in" in i for i in issues_prim)


def test_ig_loader_two_pass_forward_valueset_and_external_system(tmp_path: Path) -> None:
    """ValueSet referencing a later ValueSet resolves via two-pass incomplete_indices."""
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "ValueSet",
                    "url": "http://example.org/ValueSet/outer-vs",
                    "status": "active",
                    "compose": {
                        "include": [{"valueSet": ["http://example.org/ValueSet/inner-vs"]}]
                    },
                }
            },
            {
                "resource": {
                    "resourceType": "ValueSet",
                    "url": "http://example.org/ValueSet/inner-vs",
                    "status": "active",
                    "compose": {
                        "include": [
                            {
                                "system": "http://example.org/CodeSystem/later",
                                "concept": [{"code": "c1"}],
                            }
                        ]
                    },
                }
            },
            {
                "resource": {
                    "resourceType": "ValueSet",
                    "url": "http://example.org/ValueSet/external-only",
                    "status": "active",
                    "compose": {"include": [{"system": "http://snomed.info/sct"}]},
                }
            },
            {
                "resource": {
                    "resourceType": "StructureDefinition",
                    "url": "http://example.org/StructureDefinition/pat-outer-vs",
                    "name": "PatOuterVs",
                    "status": "active",
                    "kind": "resource",
                    "abstract": False,
                    "type": "Patient",
                    "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
                    "derivation": "constraint",
                    "differential": {
                        "element": [
                            {
                                "id": "Patient.maritalStatus",
                                "path": "Patient.maritalStatus",
                                "binding": {
                                    "strength": "required",
                                    "valueSet": "http://example.org/ValueSet/outer-vs",
                                },
                            }
                        ]
                    },
                }
            },
        ],
    }
    ig_file = tmp_path / "vs_bundle.json"
    ig_file.write_text(__import__("json").dumps(bundle), encoding="utf-8")
    profs, exts = load_compiled_ig_bundle([ig_file])
    assert "http://example.org/StructureDefinition/pat-outer-vs" in profs
    assert isinstance(exts, dict)

    prof_url = "http://example.org/StructureDefinition/pat-outer-vs"
    ok_pat = {
        "resourceType": "Patient",
        "meta": {"profile": [prof_url]},
        "maritalStatus": {"coding": [{"code": "c1"}]},
    }
    bad_pat = {
        "resourceType": "Patient",
        "meta": {"profile": [prof_url]},
        "maritalStatus": {"coding": [{"code": "bad-code"}]},
    }
    assert validate_resource(ok_pat, ig_sources=[ig_file], tx="local") == []
    bad_issues = validate_resource(bad_pat, ig_sources=[ig_file], tx="local")
    assert any("bad-code" in i for i in bad_issues)


def test_contained_warnings_and_resolve_questionnaire_by_url() -> None:
    """Contained resource warnings propagate with prefix; Questionnaire resolves by url."""
    warnings: list[str] = []
    pat = {
        "resourceType": "Patient",
        "id": "p1",
        "text": {
            "status": "generated",
            "div": "<div xmlns='http://www.w3.org/1999/xhtml'>OK</div>",
        },
        "managingOrganization": {"reference": "#org1"},
        "contained": [
            {
                "resourceType": "Organization",
                "id": "org1",
                "meta": {"profile": ["http://example.org/StructureDefinition/unknown-contained"]},
                "name": "Contained Org",
            }
        ],
    }
    issues = validate_resource(
        pat,
        unknown_profile="warning",
        _warnings_out=warnings,
    )
    assert issues == []
    assert any(w.startswith("contained[0]:") and "unknown-contained" in w for w in warnings)

    # _resolve_questionnaire: missing #id and lookup by Questionnaire.url in bundle_index
    assert (
        _resolve_questionnaire("#missing", None, [{"resourceType": "Questionnaire", "id": "q1"}])
        is None
    )
    assert _resolve_questionnaire("http://example.org/Questionnaire/q1", None, None) is None
    q_res = {
        "resourceType": "Questionnaire",
        "id": "q1",
        "url": "http://example.org/Questionnaire/q1",
    }
    bundle_index = {"urn:uuid:11111111-1111-1111-1111-111111111111": q_res}
    assert (
        _resolve_questionnaire("http://example.org/Questionnaire/q1|1.0", bundle_index, None)
        is q_res
    )
    assert (
        _resolve_questionnaire("http://example.org/Questionnaire/other", bundle_index, None) is None
    )


def test_cli_pkg_no_subcommand_and_value_bounds_edges() -> None:
    """`fhirlance pkg` without subcommand exits 2; check_value_bounds handles None."""
    with pytest.raises(SystemExit) as exc_info:
        cli_main(["pkg"])
    assert exc_info.value.code == 2
    assert check_value_bounds(True, 1, 10, "Observation.value") == []
    assert check_value_bounds(5, None, None, "Observation.value") == []
    assert check_value_bounds(5, None, 10, "Observation.value") == []
    assert check_value_bounds(5, 1, None, "Observation.value") == []
