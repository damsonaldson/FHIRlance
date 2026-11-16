"""Unit tests for StructureDefinition model and profile codegen helpers."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


def _load_codegen_module() -> Any:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "generate_models.py"
    spec = importlib.util.spec_from_file_location("generate_models", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_codegen_safe_field_name_and_pascal_case() -> None:
    mod = _load_codegen_module()
    assert mod._safe_field_name("class") == ("class_", "class")
    assert mod._safe_field_name("_internal") == ("_internal_", "_internal")
    assert mod._safe_field_name("status") == ("status", None)
    assert mod._pascal_from_path("Patient.contact.name") == "PatientContactName"


def test_codegen_profile_inheritance_merges_parent_and_child() -> None:
    mod = _load_codegen_module()
    profiles = {
        "http://example.org/base": {
            "base_type": "Observation",
            "base_definition": None,
            "required": ["Observation.status"],
            "forbidden": ["Observation.comment"],
            "max_one": ["Observation.status"],
            "fixed": {"Observation.status": "final"},
            "pattern": {},
            "type_narrowing": {"Observation.effective[x]": ["dateTime", "Period"]},
            "target_types": {"Observation.subject": ["Patient"]},
            "bindings": {},
            "slices": [{"path": "Observation.category", "min": 1, "matchers": {}}],
        },
        "http://example.org/child": {
            "base_type": "Observation",
            "base_definition": "http://example.org/base",
            "required": ["Observation.code"],
            "forbidden": [],
            "max_one": [],
            "fixed": {},
            "pattern": {"Observation.code": {"coding": [{"system": "http://loinc.org"}]}},
            "type_narrowing": {"Observation.effective[x]": ["dateTime"]},
            "target_types": {},
            "bindings": {},
            "slices": [],
        },
    }
    resolved = mod._resolve_all_profiles(profiles)
    child = resolved["http://example.org/child"]
    assert child["required"] == ["Observation.code", "Observation.status"]
    assert child["forbidden"] == ["Observation.comment"]
    assert child["fixed"] == {"Observation.status": "final"}
    assert child["type_narrowing"] == {"Observation.effective[x]": ["dateTime"]}
    assert len(child["slices"]) == 1


def test_codegen_builds_resource_model_with_choice_and_backbone() -> None:
    mod = _load_codegen_module()
    sd = {
        "id": "SampleRes",
        "snapshot": {
            "element": [
                {"path": "SampleRes"},
                {"path": "SampleRes.status", "min": 1, "max": "1", "type": [{"code": "code"}]},
                {
                    "path": "SampleRes.value[x]",
                    "min": 0,
                    "max": "1",
                    "type": [{"code": "string"}, {"code": "integer"}],
                },
                {
                    "path": "SampleRes.item",
                    "min": 0,
                    "max": "*",
                    "type": [{"code": "BackboneElement"}],
                },
                {
                    "path": "SampleRes.item.label",
                    "min": 1,
                    "max": "1",
                    "type": [{"code": "string"}],
                },
            ]
        },
    }
    emitted, root_name = mod._build_models_from_sd(sd, {}, set(), is_resource_pkg=True)
    rendered = "\n".join(emitted)
    assert root_name == "SampleRes"
    assert "class SampleResItem(FHIRBaseModel):" in rendered
    assert "class SampleRes(FHIRBaseModel):" in rendered
    assert "resourceType: Literal['SampleRes']" in rendered
    assert "valueString: StrictStr | None = None" in rendered
    assert "valueInteger: FHIRInteger | None = None" in rendered
    assert "def _check_choices" in rendered


def test_codegen_extracts_and_merges_constraints_and_preferred_bindings(tmp_path: Path) -> None:
    mod = _load_codegen_module()
    sd_parent = {
        "type": "Observation",
        "differential": {
            "element": [
                {
                    "path": "Observation",
                    "constraint": [
                        {
                            "key": "ele-1",
                            "severity": "error",
                            "human": "All FHIR elements must have a @value or children",
                            "expression": "hasValue() or (children().count() > id.count())",
                        },
                        {
                            "key": "obs-parent",
                            "severity": "warning",
                            "human": "Parent rule",
                            "expression": "status.exists()",
                        },
                    ],
                },
                {
                    "path": "Observation.category",
                    "binding": {
                        "strength": "preferred",
                        "valueSet": "http://example.org/vs/pref|1.0",
                    },
                },
            ]
        },
    }
    sd_child = {
        "type": "Observation",
        "baseDefinition": "http://example.org/parent",
        "differential": {
            "element": [
                {
                    "path": "Observation",
                    "constraint": [
                        {
                            "key": "obs-parent",
                            "severity": "error",
                            "human": "Overridden parent rule",
                            "expression": "status.exists()",
                        },
                        {
                            "key": "obs-empty",
                            "severity": "error",
                            "human": "No expression",
                            "expression": "",
                        },
                    ],
                },
                {
                    "path": "Observation.code",
                    "binding": {
                        "strength": "extensible",
                        "valueSet": "http://example.org/vs/ext",
                    },
                },
            ]
        },
    }
    profiles = {
        "http://example.org/parent": mod._extract_profile_spec(sd_parent, {}, {}),
        "http://example.org/child": mod._extract_profile_spec(sd_child, {}, {}),
    }
    resolved = mod._resolve_all_profiles(profiles)
    child = resolved["http://example.org/child"]
    assert child["preferred_bindings"] == {"category": "http://example.org/vs/pref"}
    assert child["binding_specs"] == {
        "code": {"strength": "extensible", "value_set": "http://example.org/vs/ext"}
    }
    assert child["constraints"] == [
        {
            "key": "obs-parent",
            "severity": "error",
            "human": "Overridden parent rule",
            "expression": "status.exists()",
            "path": "Observation",
        }
    ]

    r4_sd = {
        "id": "DemoRes",
        "kind": "resource",
        "abstract": False,
        "derivation": "specialization",
        "snapshot": {
            "element": [
                {
                    "path": "DemoRes",
                    "constraint": [
                        {
                            "key": "dom-6",
                            "severity": "warning",
                            "human": "Best practice",
                            "expression": "text.exists()",
                        },
                        {
                            "key": "demo-1",
                            "severity": "error",
                            "human": "Demo rule",
                            "expression": "code.exists()",
                        },
                    ],
                },
                {
                    "path": "DemoRes.language",
                    "binding": {
                        "strength": "preferred",
                        "valueSet": "http://hl7.org/fhir/ValueSet/languages|4.0.1",
                    },
                },
            ]
        },
    }
    (tmp_path / "StructureDefinition-DemoRes.json").write_text(json.dumps(r4_sd), encoding="utf-8")
    assert mod._extract_preferred_resource_bindings(tmp_path) == {
        "DemoRes": {"language": "http://hl7.org/fhir/ValueSet/languages"}
    }
    assert mod._extract_base_resource_constraints(tmp_path) == {
        "DemoRes": [
            {
                "key": "demo-1",
                "severity": "error",
                "human": "Demo rule",
                "expression": "code.exists()",
                "path": "DemoRes",
            }
        ]
    }
