"""Comprehensive tests for FHIR R4 slicing semantics and cardinality."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fhirlance.profile_engine import (
    COMPILED_PROFILES,
    CompiledProfile,
    _infer_node_type,
    _node_conforms_to_profile,
    _parse_max_count,
    _resolve_reference,
    _SliceEvalContext,
    _type_matches,
    compile_profiles,
    pattern_matches,
    resolve_typed_nodes,
    validate_single_profile,
)
from fhirlance.resource_validator import validate_resource
from fhirlance.slicing_spec import extract_slice_groups, merge_slice_groups
from fhirlance.terminology import parse_tx_options

# ==============================================================================
# Helpers
# ==============================================================================


def _compile_one(url: str, spec: dict[str, Any]) -> dict[str, CompiledProfile]:
    return compile_profiles({url: spec})


def _make_sd_package(
    tmp_path: Path,
    sds: list[dict[str, Any]],
) -> Path:
    pkg_dir = tmp_path / "test-ig"
    pkg_dir.mkdir()
    (pkg_dir / "package.json").write_text(
        json.dumps({"name": "test.slicing.ig", "version": "1.0.0", "fhirVersion": "4.0.1"}),
        encoding="utf-8",
    )
    for idx, sd in enumerate(sds):
        (pkg_dir / f"StructureDefinition-{idx}.json").write_text(
            json.dumps(sd),
            encoding="utf-8",
        )
    return pkg_dir


# ==============================================================================
# 1. Built-in IG Slicing Compilation
# ==============================================================================


class TestBuiltinIGCompilation:
    def test_builtin_profiles_have_compiled_slice_groups(self) -> None:
        expected_urls = (
            "http://hl7.org/fhir/StructureDefinition/bp",
            "http://hl7.org/fhir/StructureDefinition/lipidprofile",
            "http://hl7.org/fhir/uv/ips/StructureDefinition/Condition-uv-ips",
            "http://hl7.org/fhir/uv/ips/StructureDefinition/Composition-uv-ips",
            "http://fhir.infoway-inforoute.ca/cacore/StructureDefinition/allergyintolerance-ca-core",
        )
        for url in expected_urls:
            assert url in COMPILED_PROFILES, f"Missing built-in profile: {url}"
            assert COMPILED_PROFILES[url].slice_groups, f"Expected slice_groups on {url}"

    def test_builtin_bp_nested_component_slicing(self) -> None:
        bp_url = "http://hl7.org/fhir/StructureDefinition/bp"
        bp = COMPILED_PROFILES[bp_url]
        comp_group = next(g for g in bp.slice_groups if g.path == "Observation.component")
        sys_slice = next(s for s in comp_group.slices if s.slice_name == "SystolicBP")
        assert sys_slice.min_count == 1
        assert sys_slice.max_count == 1
        assert sys_slice.sub_groups
        sbp_sub = sys_slice.sub_groups[0]
        assert sbp_sub.path == "code.coding"
        sbp_slice = next(sl for sl in sbp_sub.slices if sl.slice_name == "SBPCode")
        assert sbp_slice.min_count == 1
        assert sbp_slice.max_count == 1
        assert any(m.sub_parts == ("code",) and m.expected == "8480-6" for m in sbp_slice.matchers)

        diastolic_slice = next(s for s in comp_group.slices if s.slice_name == "DiastolicBP")
        assert diastolic_slice.sub_groups
        dbp_sub = diastolic_slice.sub_groups[0]
        assert any(sl.slice_name == "DBPCode" and sl.min_count == 1 for sl in dbp_sub.slices)

    def test_builtin_condition_uv_ips_closed_onset_choice(self) -> None:
        cond_url = "http://hl7.org/fhir/uv/ips/StructureDefinition/Condition-uv-ips"
        cond_prof = COMPILED_PROFILES[cond_url]
        onset_group = next(g for g in cond_prof.slice_groups if g.path == "Condition.onset[x]")
        assert onset_group.rules == "closed"
        assert onset_group.is_choice is True

        base_cond: dict[str, Any] = {
            "resourceType": "Condition",
            "clinicalStatus": {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                        "code": "active",
                    }
                ]
            },
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "38341003"}]},
            "subject": {"reference": "Patient/1"},
        }
        bad_cond = {**base_cond, "onsetString": "childhood"}
        issues = validate_single_profile(bad_cond, "Condition", cond_url)
        assert any("closed slice" in i and "Condition.onset[x]" in i for i in issues)


# ==============================================================================
# 2. All 5 Discriminator Types & No-Discriminator Fallback
# ==============================================================================


class TestDiscriminatorTypes:
    def test_value_discriminator_and_nested_fallback(self) -> None:
        url = "http://example.org/StructureDefinition/obs-value-disc"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.category",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "value", "path": "coding"}],
                        "slices": [
                            {
                                "slice_name": "vs",
                                "min": 1,
                                "max": "1",
                                "matchers": {"coding.code": ("fixed", "vital-signs")},
                            }
                        ],
                    }
                ],
            },
        )
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "test"},
            "category": [{"coding": [{"code": "vital-signs"}]}],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "test"},
            "category": [{"coding": [{"code": "laboratory"}]}],
        }
        issues = validate_single_profile(obs_bad, "Observation", url, profiles)
        assert len(issues) == 1
        assert "requires at least 1" in issues[0]

    def test_pattern_discriminator_nested_dict_and_list(self) -> None:
        assert pattern_matches({"a": 1, "b": [{"x": 10, "y": 20}]}, {"b": [{"x": 10}]})
        assert not pattern_matches({"a": 1}, {"b": 2})
        assert not pattern_matches("not-a-dict", {"a": 1})
        assert not pattern_matches("not-a-list", [{"a": 1}])

        url = "http://example.org/StructureDefinition/obs-pattern-disc"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.code",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "pattern", "path": "$this"}],
                        "slices": [
                            {
                                "slice_name": "loinc",
                                "min": 1,
                                "max": "1",
                                "matchers": {
                                    "": (
                                        "pattern",
                                        {"coding": [{"system": "http://loinc.org"}]},
                                    )
                                },
                            }
                        ],
                    }
                ],
            },
        )
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"coding": [{"system": "http://snomed.info/sct", "code": "123"}]},
        }
        assert validate_single_profile(obs_bad, "Observation", url, profiles)

    def test_type_discriminator_choice_and_sub_element(self) -> None:
        assert _infer_node_type({"resourceType": "Patient"}, None) == "Patient"
        assert _infer_node_type(True, None) == "boolean"
        assert _infer_node_type(42, None) == "integer"
        assert _infer_node_type(3.14, None) == "decimal"
        assert _infer_node_type("abc", None) == "string"
        assert _infer_node_type({"foo": "bar"}, None) is None

        typed = resolve_typed_nodes(
            {"valueDecimal": 5, "extension": [{"valueInteger": 2}]},
            ("extension", "value[x]"),
        )
        assert typed == [(2, "integer")]

        url = "http://example.org/StructureDefinition/obs-type-disc"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.effective[x]",
                        "rules": "closed",
                        "ordered": False,
                        "discriminators": [{"type": "type", "path": "$this"}],
                        "slices": [
                            {
                                "slice_name": "effectiveDateTime",
                                "min": 0,
                                "max": "1",
                                "type_constraints": {"": ["dateTime"]},
                            }
                        ],
                    },
                    {
                        "path": "Observation.component",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "type", "path": "value[x]"}],
                        "slices": [
                            {
                                "slice_name": "decimalComp",
                                "min": 1,
                                "max": "1",
                                "type_constraints": {"value[x]": ["decimal"]},
                            },
                            {
                                "slice_name": "unconstrained",
                                "min": 0,
                                "max": "1",
                            },
                        ],
                    },
                ],
            },
        )
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "effectiveDateTime": "2024-01-01",
            "component": [{"code": {"text": "c"}, "valueInteger": 10}],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad_choice = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "effectivePeriod": {"start": "2024-01-01"},
            "component": [{"code": {"text": "c"}, "valueString": "hi"}],
        }
        issues = validate_single_profile(obs_bad_choice, "Observation", url, profiles)
        assert any("Observation.effective[x]" in i for i in issues)
        assert any("Observation.component" in i for i in issues)

    def test_profile_discriminator_inline_contained_bundle_and_cycle(self) -> None:
        pat_prof = "http://example.org/StructureDefinition/strict-patient"
        bundle_prof = "http://example.org/StructureDefinition/custom-bundle"
        comp_prof = "http://example.org/StructureDefinition/custom-composition"
        cycle_prof = "http://example.org/StructureDefinition/cycle-bundle"

        profiles = compile_profiles(
            {
                pat_prof: {
                    "base_type": "Patient",
                    "required": ["Patient.name"],
                },
                bundle_prof: {
                    "base_type": "Bundle",
                    "slice_groups": [
                        {
                            "path": "Bundle.entry",
                            "rules": "open",
                            "ordered": False,
                            "discriminators": [{"type": "profile", "path": "resource"}],
                            "slices": [
                                {
                                    "slice_name": "patientEntry",
                                    "min": 1,
                                    "max": "1",
                                    "profile_constraints": {"resource": [pat_prof]},
                                },
                                {
                                    "slice_name": "hl7BaseObs",
                                    "min": 0,
                                    "max": "1",
                                    "profile_constraints": {
                                        "resource": [
                                            "http://hl7.org/fhir/StructureDefinition/Observation"
                                        ]
                                    },
                                },
                            ],
                        }
                    ],
                },
                comp_prof: {
                    "base_type": "Observation",
                    "slice_groups": [
                        {
                            "path": "Observation.hasMember",
                            "rules": "open",
                            "ordered": False,
                            "discriminators": [{"type": "profile", "path": "$this.resolve()"}],
                            "slices": [
                                {
                                    "slice_name": "patientMember",
                                    "min": 1,
                                    "max": "1",
                                    "profile_constraints": {"": [pat_prof]},
                                },
                                {
                                    "slice_name": "noProfileConstraint",
                                    "min": 0,
                                    "max": "1",
                                },
                            ],
                        }
                    ],
                },
                cycle_prof: {
                    "base_type": "Bundle",
                    "slice_groups": [
                        {
                            "path": "Bundle.entry",
                            "rules": "open",
                            "ordered": False,
                            "discriminators": [{"type": "profile", "path": "resource"}],
                            "slices": [
                                {
                                    "slice_name": "selfRef",
                                    "min": 1,
                                    "max": "1",
                                    "profile_constraints": {"resource": [cycle_prof]},
                                }
                            ],
                        }
                    ],
                },
            }
        )

        # Inline profile match in Bundle.entry
        bundle_ok = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {"resource": {"resourceType": "Patient", "name": [{"family": "Doe"}]}},
                {"resource": {"resourceType": "Observation", "status": "final"}},
            ],
        }
        assert validate_single_profile(bundle_ok, "Bundle", bundle_prof, profiles) == []

        # Patient missing required name fails profile discriminator
        bundle_bad = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": {"resourceType": "Patient"}}],
        }
        assert validate_single_profile(bundle_bad, "Bundle", bundle_prof, profiles)

        # Contained resource resolution via $this.resolve()
        obs_contained = {
            "resourceType": "Observation",
            "status": "final",
            "contained": [{"resourceType": "Patient", "id": "p1", "name": [{"family": "A"}]}],
            "hasMember": [{"reference": "#p1"}],
        }
        assert validate_single_profile(obs_contained, "Observation", comp_prof, profiles) == []

        # Unresolved external reference -> non-match
        obs_unresolved = {
            "resourceType": "Observation",
            "status": "final",
            "hasMember": [{"reference": "Patient/missing"}],
        }
        assert validate_single_profile(obs_unresolved, "Observation", comp_prof, profiles)

        # Bundle index resolution via $this.resolve()
        bundle_index = {"Patient/p2": {"resourceType": "Patient", "name": [{"family": "B"}]}}
        obs_bundle_ref = {
            "resourceType": "Observation",
            "status": "final",
            "hasMember": [{"reference": "Patient/p2"}],
        }
        assert (
            validate_single_profile(
                obs_bundle_ref,
                "Observation",
                comp_prof,
                profiles,
                bundle_index=bundle_index,
            )
            == []
        )

        # Recursive cycle guard terminates cleanly
        cycle_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [{"resource": {"resourceType": "Bundle", "type": "collection"}}],
        }
        assert validate_single_profile(cycle_bundle, "Bundle", cycle_prof, profiles) == []

    def test_exists_discriminator(self) -> None:
        url = "http://example.org/StructureDefinition/obs-exists-disc"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.component",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "exists", "path": "value[x]"}],
                        "slices": [
                            {
                                "slice_name": "withValue",
                                "min": 1,
                                "max": "1",
                                "exists_constraints": {"value[x]": True},
                            },
                            {
                                "slice_name": "withoutValue",
                                "min": 1,
                                "max": "1",
                                "exists_constraints": {"value[x]": False},
                            },
                            {
                                "slice_name": "noConstraint",
                                "min": 0,
                                "max": "1",
                            },
                        ],
                    }
                ],
            },
        )
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [
                {"code": {"text": "a"}, "valueInteger": 1},
                {"code": {"text": "b"}},
            ],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_missing_without = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [{"code": {"text": "a"}, "valueInteger": 1}],
        }
        assert validate_single_profile(obs_missing_without, "Observation", url, profiles)

    def test_no_discriminator_fallback_and_unknown_disc(self) -> None:
        pat_prof = "http://example.org/StructureDefinition/inner-coding"
        url = "http://example.org/StructureDefinition/obs-no-disc"
        profiles = compile_profiles(
            {
                pat_prof: {
                    "base_type": "Coding",
                    "required": ["Coding.code"],
                },
                url: {
                    "base_type": "Observation",
                    "slice_groups": [
                        {
                            "path": "Observation.component",
                            "rules": "open",
                            "ordered": False,
                            "discriminators": [],
                            "slices": [
                                {
                                    "slice_name": "fullMatch",
                                    "min": 1,
                                    "max": "1",
                                    "matchers": {"code.text": ("fixed", "sys")},
                                    "type_constraints": {"value[x]": ["integer"]},
                                    "profile_constraints": {"code.coding": [pat_prof]},
                                    "exists_constraints": {"value[x]": True},
                                },
                                {
                                    "slice_name": "emptyConstraints",
                                    "min": 0,
                                    "max": "1",
                                },
                            ],
                        }
                    ],
                },
            }
        )
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [
                {
                    "code": {"text": "sys", "coding": [{"code": "8480-6"}]},
                    "valueInteger": 120,
                }
            ],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [
                {
                    "code": {"text": "sys", "coding": [{"display": "missing code"}]},
                    "valueInteger": 120,
                }
            ],
        }
        assert validate_single_profile(obs_bad, "Observation", url, profiles)


# ==============================================================================
# 3. Slice max Cardinality & Legacy _check_slices
# ==============================================================================


class TestSliceMaxCardinality:
    def test_slice_max_zero_one_two_and_unlimited(self) -> None:
        url = "http://example.org/StructureDefinition/obs-max-card"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.category",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "value", "path": "coding.code"}],
                        "slices": [
                            {
                                "slice_name": "forbiddenCat",
                                "min": 0,
                                "max": "0",
                                "matchers": {"coding.code": ("fixed", "banned")},
                            },
                            {
                                "slice_name": "oneCat",
                                "min": 0,
                                "max": "1",
                                "matchers": {"coding.code": ("fixed", "one")},
                            },
                            {
                                "slice_name": "twoCat",
                                "min": 0,
                                "max": "2",
                                "matchers": {"coding.code": ("fixed", "two")},
                            },
                            {
                                "slice_name": "manyCat",
                                "min": 0,
                                "max": "*",
                                "matchers": {"coding.code": ("fixed", "many")},
                            },
                        ],
                    }
                ],
            },
        )
        ok_obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "one"}]},
                {"coding": [{"code": "two"}]},
                {"coding": [{"code": "two"}]},
                {"coding": [{"code": "many"}]},
                {"coding": [{"code": "many"}]},
                {"coding": [{"code": "many"}]},
            ],
        }
        assert validate_single_profile(ok_obs, "Observation", url, profiles) == []

        bad_obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "banned"}]},
                {"coding": [{"code": "one"}]},
                {"coding": [{"code": "one"}]},
                {"coding": [{"code": "two"}]},
                {"coding": [{"code": "two"}]},
                {"coding": [{"code": "two"}]},
            ],
        }
        issues = validate_single_profile(bad_obs, "Observation", url, profiles)
        assert any("allows at most 0" in i for i in issues)
        assert any("allows at most 1" in i for i in issues)
        assert any("allows at most 2" in i for i in issues)

    def test_legacy_check_slices_max_count(self) -> None:
        url = "http://example.org/StructureDefinition/legacy-slice"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slices": [
                    {
                        "path": "Observation.category",
                        "min": 1,
                        "max": "1",
                        "matchers": {"coding.code": ("fixed", "vital-signs")},
                    }
                ],
            },
        )
        obs_two = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "vital-signs"}]},
                {"coding": [{"code": "vital-signs"}]},
            ],
        }
        issues = validate_single_profile(obs_two, "Observation", url, profiles)
        assert any("allows at most 1" in i for i in issues)


# ==============================================================================
# 4. Slicing rules & ordered
# ==============================================================================


class TestSlicingRulesAndOrdered:
    def _make_group_profile(
        self, rules: str, ordered: bool
    ) -> tuple[str, dict[str, CompiledProfile]]:
        url = f"http://example.org/StructureDefinition/obs-{rules}-{ordered}"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.category",
                        "rules": rules,
                        "ordered": ordered,
                        "discriminators": [{"type": "value", "path": "coding.code"}],
                        "slices": [
                            {
                                "slice_name": "first",
                                "min": 0,
                                "max": "*",
                                "matchers": {"coding.code": ("fixed", "A")},
                            },
                            {
                                "slice_name": "second",
                                "min": 0,
                                "max": "*",
                                "matchers": {"coding.code": ("fixed", "B")},
                            },
                        ],
                    }
                ],
            },
        )
        return url, profiles

    def test_closed_rejects_unmatched(self) -> None:
        url, profiles = self._make_group_profile("closed", False)
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [{"coding": [{"code": "A"}]}, {"coding": [{"code": "OTHER"}]}],
        }
        issues = validate_single_profile(obs, "Observation", url, profiles)
        assert any("closed slice" in i and "1 unmatched" in i for i in issues)

    def test_open_at_end_allows_trailing_and_rejects_interleaved(self) -> None:
        url, profiles = self._make_group_profile("openAtEnd", False)
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [{"coding": [{"code": "A"}]}, {"coding": [{"code": "EXTRA"}]}],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "EXTRA"}]},
                {"coding": [{"code": "A"}]},
            ],
        }
        issues = validate_single_profile(obs_bad, "Observation", url, profiles)
        assert any("openAtEnd slice" in i for i in issues)

    def test_open_allows_unmatched_anywhere(self) -> None:
        url, profiles = self._make_group_profile("open", False)
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "EXTRA"}]},
                {"coding": [{"code": "B"}]},
                {"coding": [{"code": "A"}]},
            ],
        }
        assert validate_single_profile(obs, "Observation", url, profiles) == []

    def test_ordered_enforces_non_decreasing_slice_order(self) -> None:
        url, profiles = self._make_group_profile("open", True)
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "A"}]},
                {"coding": [{"code": "A"}]},
                {"coding": [{"code": "B"}]},
            ],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "category": [
                {"coding": [{"code": "B"}]},
                {"coding": [{"code": "A"}]},
            ],
        }
        issues = validate_single_profile(obs_bad, "Observation", url, profiles)
        assert any("ordered slice" in i for i in issues)


# ==============================================================================
# 5. Multi-level Nested Sub-Slicing
# ==============================================================================


class TestNestedSubSlicing:
    def test_synthetic_two_level_nested_sub_slicing(self) -> None:
        url = "http://example.org/StructureDefinition/obs-nested-sub"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.component",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "value", "path": "code.text"}],
                        "slices": [
                            {
                                "slice_name": "panel",
                                "min": 1,
                                "max": "1",
                                "matchers": {"code.text": ("fixed", "panel")},
                                "sub_groups": [
                                    {
                                        "path": "code.coding",
                                        "rules": "closed",
                                        "ordered": False,
                                        "discriminators": [{"type": "value", "path": "code"}],
                                        "slices": [
                                            {
                                                "slice_name": "primary",
                                                "min": 1,
                                                "max": "1",
                                                "matchers": {"code": ("fixed", "P1")},
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            },
        )
        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [
                {"code": {"text": "panel", "coding": [{"code": "P1"}]}},
            ],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

        obs_bad_inner = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [
                {
                    "code": {
                        "text": "panel",
                        "coding": [{"code": "P1"}, {"code": "EXTRA"}],
                    }
                },
            ],
        }
        issues = validate_single_profile(obs_bad_inner, "Observation", url, profiles)
        assert any("closed slice" in i and "code.coding" in i for i in issues)


# ==============================================================================
# 6. Inheritance (slicing_spec) & Runtime -ig Bundle Resolution
# ==============================================================================


class TestSlicingSpecAndRuntimeIG:
    def test_extract_slice_groups_edges_and_merge(self) -> None:
        elements: list[dict[str, Any]] = [
            {"id": ""},
            {
                "id": "Observation.component",
                "slicing": {
                    "rules": "invalid-rule",
                    "ordered": True,
                    "discriminator": [{"type": "value"}],
                },
            },
            {
                "id": "Observation.component:sys",
                "sliceName": "sysCustom",
                "min": 1,
                "max": "2",
            },
            {
                "id": "Observation.component:sys.code.coding",
                "slicing": {
                    "rules": "closed",
                    "discriminator": [{"type": "pattern", "path": "$this"}],
                },
            },
            {
                "id": "Observation.component:sys.code.coding:loinc",
                "min": 1,
                "max": "1",
                "patternCoding": {"system": "http://loinc.org"},
                "type": [{"code": "Coding", "profile": ["http://example.org/coding"]}],
            },
            {
                "id": "Observation.component:sys.value[x]",
                "min": 0,
                "max": "0",
            },
            {
                "id": "Observation.note",
                "slicing": {"rules": "open", "discriminator": [{"type": "value", "path": "text"}]},
            },
            {
                "id": "Observation.note:optional",
                "min": 0,
                "max": "*",
                "fixedString": "kept",
            },
            {
                "id": "Observation.performer",
                "slicing": {"rules": "open"},
            },
            {
                "id": "Observation.performer:noop",
                "min": 0,
                "max": "*",
            },
        ]
        groups = extract_slice_groups(elements)
        assert len(groups) == 2  # Observation.performer pruned as empty no-op
        comp = groups[0]
        assert comp["rules"] == "open"  # invalid-rule fell back to open
        assert comp["ordered"] is True
        assert comp["discriminators"] == [{"type": "value", "path": "$this"}]
        sys_sl = comp["slices"][0]
        assert sys_sl["slice_name"] == "sysCustom"
        assert sys_sl["max"] == "2"
        assert sys_sl["exists_constraints"] == {"value[x]": False}
        assert len(sys_sl["sub_groups"]) == 1

        parent_groups = [
            {
                "path": "Observation.component",
                "rules": "open",
                "ordered": False,
                "discriminators": [{"type": "value", "path": "code.text"}],
                "slices": [
                    {
                        "slice_name": "sys",
                        "min": 0,
                        "max": "2",
                        "matchers": {"code.text": ("fixed", "sys")},
                        "sub_groups": [],
                    }
                ],
            }
        ]
        child_groups = [
            {
                "path": "Observation.component",
                "rules": "closed",
                "ordered": True,
                "discriminators": [],
                "slices": [
                    {
                        "slice_name": "sys",
                        "min": 1,
                        "max": "1",
                        "matchers": {},
                        "sub_groups": [],
                    },
                    {
                        "slice_name": "dia",
                        "min": 1,
                        "max": "1",
                        "matchers": {"code.text": ("fixed", "dia")},
                        "sub_groups": [],
                    },
                ],
            },
            {
                "path": "Observation.category",
                "rules": "openAtEnd",
                "ordered": False,
                "discriminators": [],
                "slices": [],
            },
        ]
        merged = merge_slice_groups(parent_groups, child_groups)
        assert len(merged) == 2
        m_comp = next(g for g in merged if g["path"] == "Observation.component")
        assert m_comp["rules"] == "closed"
        assert m_comp["ordered"] is True
        assert m_comp["discriminators"] == [{"type": "value", "path": "code.text"}]
        assert len(m_comp["slices"]) == 2
        m_sys = next(s for s in m_comp["slices"] if s["slice_name"] == "sys")
        assert m_sys["min"] == 1
        assert m_sys["max"] == "1"

    def test_runtime_ig_bundle_with_profile_discriminator(self, tmp_path: Path) -> None:
        pat_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/custom-pat",
            "name": "CustomPat",
            "status": "active",
            "kind": "resource",
            "abstract": False,
            "type": "Patient",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Patient",
            "derivation": "constraint",
            "differential": {
                "element": [
                    {"id": "Patient.name", "path": "Patient.name", "min": 1},
                ]
            },
        }
        obs_sd = {
            "resourceType": "StructureDefinition",
            "url": "http://example.org/fhir/StructureDefinition/custom-obs",
            "name": "CustomObs",
            "status": "active",
            "kind": "resource",
            "abstract": False,
            "type": "Observation",
            "baseDefinition": "http://hl7.org/fhir/StructureDefinition/Observation",
            "derivation": "constraint",
            "differential": {
                "element": [
                    {
                        "id": "Observation.subject",
                        "path": "Observation.subject",
                        "min": 1,
                        "type": [
                            {
                                "code": "Reference",
                                "targetProfile": [
                                    "http://example.org/fhir/StructureDefinition/custom-pat"
                                ],
                            }
                        ],
                    },
                    {
                        "id": "Observation.hasMember",
                        "path": "Observation.hasMember",
                        "slicing": {
                            "discriminator": [{"type": "profile", "path": "$this.resolve()"}],
                            "rules": "closed",
                            "ordered": True,
                        },
                    },
                    {
                        "id": "Observation.hasMember:patRef",
                        "path": "Observation.hasMember",
                        "sliceName": "patRef",
                        "min": 1,
                        "max": "1",
                        "type": [
                            {
                                "code": "Reference",
                                "targetProfile": [
                                    "http://example.org/fhir/StructureDefinition/custom-pat"
                                ],
                            }
                        ],
                    },
                ]
            },
        }
        ig_dir = _make_sd_package(tmp_path, [pat_sd, obs_sd])

        valid_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "Patient/pat-1",
                    "resource": {
                        "resourceType": "Patient",
                        "id": "pat-1",
                        "name": [{"family": "Smith"}],
                    },
                },
                {
                    "fullUrl": "Observation/obs-1",
                    "resource": {
                        "resourceType": "Observation",
                        "id": "obs-1",
                        "meta": {
                            "profile": ["http://example.org/fhir/StructureDefinition/custom-obs"]
                        },
                        "status": "final",
                        "code": {"text": "test"},
                        "subject": {"reference": "Patient/pat-1"},
                        "hasMember": [{"reference": "Patient/pat-1"}],
                    },
                },
            ],
        }
        assert validate_resource(valid_bundle, ig_sources=[ig_dir], tx="off") == []

        # Patient missing name causes $this.resolve() profile discriminator to fail
        invalid_bundle = {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": [
                {
                    "fullUrl": "Patient/pat-1",
                    "resource": {"resourceType": "Patient", "id": "pat-1"},
                },
                valid_bundle["entry"][1],
            ],
        }
        issues = validate_resource(invalid_bundle, ig_sources=[ig_dir], tx="off")
        assert any("Observation.hasMember" in i for i in issues)


# ==============================================================================
# 7. Edge Cases for High Branch Coverage
# ==============================================================================


class TestSlicingEdgeCases:
    def test_resolve_reference_and_type_helpers(self) -> None:
        assert _parse_max_count(3) == 3
        assert _parse_max_count("abc") is None
        assert _type_matches({}, None, ("Patient",)) is False

        root: dict[str, Any] = {
            "resourceType": "Observation",
            "contained": [{"resourceType": "Patient", "id": "p1"}],
        }
        inline = {"resourceType": "Patient", "id": "inline"}
        assert _resolve_reference(inline, root, None) is inline
        assert _resolve_reference("#p1", root, None) == {"resourceType": "Patient", "id": "p1"}
        assert _resolve_reference("#missing", root, None) is None
        assert _resolve_reference("", root, None) is None
        assert _resolve_reference(123, root, None) is None

        typed = resolve_typed_nodes(
            {"value": 1, "valueList": ["a", "b"], "valueNested": {"sub": 1}},
            ("value[x]",),
        )
        assert ("a", "List") in typed
        assert ("b", "List") in typed
        typed_tail = resolve_typed_nodes(
            {"valueObj": {"sub": "x"}},
            ("value[x]", "sub"),
        )
        assert typed_tail == [("x", None)]

        no_base_prof = "http://example.org/StructureDefinition/no-base"
        profiles = _compile_one(no_base_prof, {"required": ["Patient.name"]})
        ctx = _SliceEvalContext(
            root_resource=root,
            compiled_profiles=profiles,
            tx_options=parse_tx_options("off"),
            bundle_index=None,
            visited_profiles=frozenset(),
        )
        assert _node_conforms_to_profile({}, "http://example.org/unknown", ctx) is True
        assert _node_conforms_to_profile({}, no_base_prof, ctx) is False

    def test_resolve_target_value_type_unknown_disc_and_no_disc_mismatches(self) -> None:
        url = "http://example.org/StructureDefinition/edge-slicing"
        profiles = _compile_one(
            url,
            {
                "base_type": "Observation",
                "slice_groups": [
                    {
                        "path": "Observation.hasMember",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "value", "path": "status.resolve()"}],
                        "slices": [
                            {
                                "slice_name": "finalMember",
                                "min": 1,
                                "max": "1",
                                "matchers": {"status": ("fixed", "final")},
                            }
                        ],
                    },
                    {
                        "path": "Observation.derivedFrom",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "type", "path": "$this.resolve()"}],
                        "slices": [
                            {
                                "slice_name": "patDerived",
                                "min": 1,
                                "max": "1",
                                "type_constraints": {"": ["Patient"]},
                            }
                        ],
                    },
                    {
                        "path": "Observation.note",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "unknown", "path": "$this"}],
                        "slices": [{"slice_name": "s1", "min": 0, "max": "1"}],
                    },
                    {
                        "path": "Observation.category",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [{"type": "value", "path": "text"}],
                        "slices": [
                            {
                                "slice_name": "catA",
                                "min": 1,
                                "max": "1",
                                "matchers": {
                                    "text": ("fixed", "A"),
                                    "coding.code": ("fixed", "required-code"),
                                },
                            }
                        ],
                    },
                    {
                        "path": "Observation.component",
                        "rules": "open",
                        "ordered": False,
                        "discriminators": [],
                        "slices": [
                            {
                                "slice_name": "noDisc",
                                "min": 0,
                                "max": "1",
                                "matchers": {"code.text": ("fixed", "m")},
                                "type_constraints": {"value[x]": ["integer"]},
                            },
                            {
                                "slice_name": "noDiscExists",
                                "min": 0,
                                "max": "1",
                                "matchers": {"code.text": ("fixed", "e")},
                                "exists_constraints": {"value[x]": True},
                            },
                        ],
                    },
                ],
            },
        )
        obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "contained": [
                {"resourceType": "Patient", "id": "p1"},
                {"resourceType": "Observation", "id": "o1", "status": "final"},
            ],
            "hasMember": [{"status": "#o1"}],
            "derivedFrom": [{"reference": "#p1"}],
            "note": [{"text": "hello"}],
            "category": [{"text": "A", "coding": [{"code": "wrong"}]}],
            "component": [
                {"code": {"text": "other"}},
                {"code": {"text": "m"}, "valueString": "bad-type"},
                {"code": {"text": "e"}},
            ],
        }
        issues = validate_single_profile(obs, "Observation", url, profiles)
        assert any("does not satisfy slice constraints" in i for i in issues)

    def test_slicing_spec_misc_branches(self) -> None:
        elements: list[dict[str, Any]] = [
            {"id": "Observation.component", "slicing": {"rules": "open", "discriminator": "bad"}},
            {
                "id": "Observation.component:c1",
                "min": 0,
                "max": "2",
                "type": ["not-a-dict", {"code": ""}],
            },
            {
                "id": "Observation.component:c1.sub",
                "slicing": {"rules": "closed", "discriminator": [{"type": "value", "path": "x"}]},
            },
            {
                "id": "Observation.component:c1.sub:s1",
                "min": 0,
                "max": "1",
                "fixedString": "v",
            },
        ]
        groups = extract_slice_groups(elements)
        assert len(groups) == 1
        assert groups[0]["slices"][0]["max"] == "2"
        assert groups[0]["slices"][0]["sub_groups"][0]["rules"] == "closed"

    def test_slice_internal_non_discriminator_constraints_enforced(self) -> None:
        ext_prof = "http://example.org/StructureDefinition/req-ext"
        obs_prof = "http://example.org/StructureDefinition/slice-internal"
        profiles = compile_profiles(
            {
                ext_prof: {
                    "base_type": "Extension",
                    "required": ["Extension.value[x]"],
                },
                obs_prof: {
                    "base_type": "Observation",
                    "slice_groups": [
                        {
                            "path": "Observation.component",
                            "rules": "open",
                            "ordered": False,
                            "discriminators": [{"type": "value", "path": "code.text"}],
                            "slices": [
                                {
                                    "slice_name": "sys",
                                    "min": 1,
                                    "max": "1",
                                    "matchers": {"code.text": ("fixed", "sys")},
                                    "exists_constraints": {"value[x]": True},
                                    "type_constraints": {"value[x]": ["Quantity"]},
                                    "profile_constraints": {"extension": [ext_prof]},
                                }
                            ],
                        }
                    ],
                },
            }
        )
        valid_obs = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "bp"},
            "component": [
                {
                    "code": {"text": "sys"},
                    "valueQuantity": {"value": 120},
                    "extension": [{"url": "http://example.org/ext", "valueString": "ok"}],
                }
            ],
        }
        assert validate_single_profile(valid_obs, "Observation", obs_prof, profiles) == []

        # Missing exists_constraints (no value[x])
        no_val = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "bp"},
            "component": [
                {
                    "code": {"text": "sys"},
                    "extension": [{"url": "http://example.org/ext", "valueString": "ok"}],
                }
            ],
        }
        assert any(
            "does not satisfy slice constraints" in i
            for i in validate_single_profile(no_val, "Observation", obs_prof, profiles)
        )

        # Wrong type_constraints (valueString instead of Quantity)
        bad_type = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "bp"},
            "component": [
                {
                    "code": {"text": "sys"},
                    "valueString": "120",
                    "extension": [{"url": "http://example.org/ext", "valueString": "ok"}],
                }
            ],
        }
        assert any(
            "does not satisfy slice constraints" in i
            for i in validate_single_profile(bad_type, "Observation", obs_prof, profiles)
        )

        # Failing profile_constraints (extension missing required value[x])
        bad_ext = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "bp"},
            "component": [
                {
                    "code": {"text": "sys"},
                    "valueQuantity": {"value": 120},
                    "extension": [{"url": "http://example.org/ext"}],
                }
            ],
        }
        assert any(
            "does not satisfy slice constraints" in i
            for i in validate_single_profile(bad_ext, "Observation", obs_prof, profiles)
        )

    def test_open_optional_parent_slice_preserved_and_inherited(self) -> None:
        parent_els: list[dict[str, Any]] = [
            {
                "id": "Observation.component",
                "slicing": {
                    "rules": "open",
                    "discriminator": [{"type": "value", "path": "code.text"}],
                },
            },
            {
                "id": "Observation.component:opt",
                "min": 0,
                "max": "*",
            },
            {
                "id": "Observation.component:opt.code.text",
                "fixedString": "opt-code",
            },
        ]
        child_els: list[dict[str, Any]] = [
            {
                "id": "Observation.component:opt",
                "min": 1,
            }
        ]
        parent_groups = extract_slice_groups(parent_els)
        assert len(parent_groups) == 1
        child_groups = extract_slice_groups(child_els)
        merged = merge_slice_groups(parent_groups, child_groups)

        url = "http://example.org/StructureDefinition/child-inherited"
        profiles = _compile_one(url, {"base_type": "Observation", "slice_groups": merged})
        obs_missing = {"resourceType": "Observation", "status": "final", "code": {"text": "x"}}
        issues = validate_single_profile(obs_missing, "Observation", url, profiles)
        assert any("requires at least 1 matching item(s)" in i for i in issues)

    def test_max_zero_no_discriminator_fallback_rejects_match(self) -> None:
        els: list[dict[str, Any]] = [
            {"id": "Observation.component", "slicing": {"rules": "open"}},
            {"id": "Observation.component:banned", "min": 0, "max": "0"},
            {"id": "Observation.component:banned.code.text", "fixedString": "forbidden"},
        ]
        groups = extract_slice_groups(els)
        assert groups[0]["slices"][0]["exists_constraints"] == {}

        url = "http://example.org/StructureDefinition/max-zero-no-disc"
        profiles = _compile_one(url, {"base_type": "Observation", "slice_groups": groups})

        obs_bad = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [{"code": {"text": "forbidden"}}],
        }
        issues = validate_single_profile(obs_bad, "Observation", url, profiles)
        assert any("allows at most 0 matching item(s)" in i for i in issues)

        obs_ok = {
            "resourceType": "Observation",
            "status": "final",
            "code": {"text": "x"},
            "component": [{"code": {"text": "allowed"}}],
        }
        assert validate_single_profile(obs_ok, "Observation", url, profiles) == []

    def test_choice_typed_nodes_ignores_lowercase_suffix(self) -> None:
        typed = resolve_typed_nodes(
            {"onsetfoo": "ignored", "onsetDateTime": "2024-01-01"},
            ("onset[x]",),
        )
        assert typed == [("2024-01-01", "dateTime")]
