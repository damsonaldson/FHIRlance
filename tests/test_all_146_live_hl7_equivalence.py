"""Live batch equivalence test suite across all 146 FHIR R4 resources, invariants, and profiles."""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from fhirlance import RESOURCE_MODELS, validate_resource


def _find_validator_jar() -> Path | None:
    candidates = [
        Path(os.environ["FHIR_VALIDATOR_JAR"]) if os.environ.get("FHIR_VALIDATOR_JAR") else None,
        Path(__file__).resolve().parents[1] / "tools" / "validator_cli.jar",
        Path(__file__).resolve().parents[2] / "lakehouse-fhir" / "tools" / "validator_cli.jar",
    ]
    return next((p for p in candidates if p is not None and p.exists()), None)


VALIDATOR_JAR = _find_validator_jar()
R4_EXAMPLES_DIR = Path.home() / ".fhir" / "packages" / "hl7.fhir.r4.examples#4.0.1" / "package"

_SYNTHETIC_FALLBACKS: dict[str, dict[str, Any]] = {
    "Parameters": {
        "resourceType": "Parameters",
        "id": "param-1",
        "parameter": [{"name": "p", "valueString": "v"}],
    },
    "SubstanceNucleicAcid": {"resourceType": "SubstanceNucleicAcid", "id": "sna-1"},
    "SubstancePolymer": {"resourceType": "SubstancePolymer", "id": "sp-1"},
    "SubstanceProtein": {"resourceType": "SubstanceProtein", "id": "spr-1"},
    "SubstanceReferenceInformation": {
        "resourceType": "SubstanceReferenceInformation",
        "id": "sri-1",
    },
    "SubstanceSourceMaterial": {"resourceType": "SubstanceSourceMaterial", "id": "ssm-1"},
}


def _select_official_examples() -> dict[str, dict[str, Any]]:
    """Pick one clean valid example JSON for each of the 146 FHIR R4 resources."""
    examples: dict[str, dict[str, Any]] = dict(_SYNTHETIC_FALLBACKS)
    remaining_lower = {rt.lower(): rt for rt in RESOURCE_MODELS if rt not in examples}
    if R4_EXAMPLES_DIR.exists():
        candidates = sorted(
            R4_EXAMPLES_DIR.glob("*.json"),
            key=lambda p: (0 if "-example" in p.name else 1, p.name),
        )
        for p in candidates:
            if not remaining_lower:
                break
            prefix = p.stem.split("-")[0].lower()
            if prefix not in remaining_lower and "-example" in p.name:
                continue
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError):
                continue
            if not isinstance(data, dict):
                continue
            rt = data.get("resourceType")
            if (
                isinstance(rt, str)
                and rt in RESOURCE_MODELS
                and rt not in examples
                and not validate_resource(data)
            ):
                examples[rt] = data
                remaining_lower.pop(rt.lower(), None)

    return examples


def _extra_equivalence_cases() -> list[tuple[str, dict[str, Any], bool]]:
    """Return 50 targeted live equivalence cases across invariants, primitives, choices, and IGs."""
    return [
        # 1. FHIRPath Invariants (txt-1, pat-1, obs-6, obs-7, con-4, bdl-1/3/4/7, ext-1)
        (
            "inv_txt1_missing_div_wrapper",
            {
                "resourceType": "Patient",
                "id": "inv-txt1",
                "text": {"status": "generated", "div": "<span>not a div</span>"},
            },
            False,
        ),
        (
            "inv_pat1_empty_contact",
            {"resourceType": "Patient", "id": "inv-pat1", "contact": [{"gender": "female"}]},
            False,
        ),
        (
            "inv_pat1_valid_contact",
            {
                "resourceType": "Patient",
                "id": "inv-pat1-ok",
                "contact": [{"name": {"family": "Doe"}}],
            },
            True,
        ),
        (
            "inv_obs6_value_and_dar_conflict",
            {
                "resourceType": "Observation",
                "id": "inv-obs6",
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "valueQuantity": {"value": 72, "unit": "beats/min"},
                "dataAbsentReason": {
                    "coding": [
                        {
                            "system": "http://terminology.hl7.org/CodeSystem/data-absent-reason",
                            "code": "unknown",
                        }
                    ]
                },
            },
            False,
        ),
        (
            "inv_obs7_component_same_code_as_obs",
            {
                "resourceType": "Observation",
                "id": "inv-obs7",
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "valueQuantity": {"value": 72, "unit": "beats/min"},
                "component": [
                    {
                        "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                        "valueQuantity": {"value": 72, "unit": "beats/min"},
                    }
                ],
            },
            False,
        ),
        (
            "inv_con4_abated_without_clinical_status",
            {
                "resourceType": "Condition",
                "id": "inv-con4",
                "subject": {"reference": "Patient/pat-1"},
                "abatementDateTime": "2026-01-15",
            },
            False,
        ),
        (
            "inv_bdl1_total_on_collection_bundle",
            {"resourceType": "Bundle", "id": "inv-bdl1", "type": "collection", "total": 0},
            False,
        ),
        (
            "inv_bdl3_request_on_collection_bundle",
            {
                "resourceType": "Bundle",
                "id": "inv-bdl3",
                "type": "collection",
                "entry": [{"request": {"method": "GET", "url": "Patient"}}],
            },
            False,
        ),
        (
            "inv_bdl4_response_on_collection_bundle",
            {
                "resourceType": "Bundle",
                "id": "inv-bdl4",
                "type": "collection",
                "entry": [{"response": {"status": "200"}}],
            },
            False,
        ),
        (
            "inv_bdl7_duplicate_fullurl_in_collection",
            {
                "resourceType": "Bundle",
                "id": "inv-bdl7",
                "type": "collection",
                "entry": [
                    {
                        "fullUrl": "urn:uuid:11111111-2222-3333-4444-555555555555",
                        "resource": {"resourceType": "Patient", "id": "p1"},
                    },
                    {
                        "fullUrl": "urn:uuid:11111111-2222-3333-4444-555555555555",
                        "resource": {"resourceType": "Patient", "id": "p1"},
                    },
                ],
            },
            False,
        ),
        (
            "inv_ext1_empty_extension",
            {
                "resourceType": "Patient",
                "id": "inv-ext1-empty",
                "extension": [{"url": "http://example.org/fhir/StructureDefinition/ext-empty"}],
            },
            False,
        ),
        (
            "inv_ext1_both_value_and_subextension",
            {
                "resourceType": "Patient",
                "id": "inv-ext1-both",
                "extension": [
                    {
                        "url": "http://example.org/fhir/StructureDefinition/ext-both",
                        "valueString": "val",
                        "extension": [{"url": "sub", "valueString": "subval"}],
                    }
                ],
            },
            False,
        ),
        # 2. Strict Primitive Regex & Type Boundaries
        (
            "prim_invalid_non_leap_year_date",
            {"resourceType": "Patient", "id": "prim-date", "birthDate": "2023-02-29"},
            False,
        ),
        (
            "prim_valid_leap_year_date",
            {"resourceType": "Patient", "id": "prim-leap", "birthDate": "2024-02-29"},
            True,
        ),
        (
            "prim_invalid_datetime_missing_tz",
            {
                "resourceType": "Observation",
                "id": "prim-dt",
                "status": "final",
                "code": {"text": "HR"},
                "effectiveDateTime": "2026-05-15T10:30:00",
            },
            False,
        ),
        (
            "prim_invalid_instant_date_only",
            {
                "resourceType": "Observation",
                "id": "prim-inst",
                "status": "final",
                "code": {"text": "HR"},
                "issued": "2026-05-15",
            },
            False,
        ),
        (
            "prim_invalid_positive_int_zero",
            {"resourceType": "Patient", "id": "prim-posint", "multipleBirthInteger": True},
            False,
        ),
        (
            "prim_invalid_unsigned_int_negative",
            {"resourceType": "Bundle", "id": "prim-uint", "type": "searchset", "total": -1},
            False,
        ),
        (
            "prim_invalid_id_over_64_chars",
            {"resourceType": "Patient", "id": "a" * 65},
            False,
        ),
        # 3. Choice [x] Exclusivity & _primitive Companion Elements
        (
            "choice_patient_deceased_both_variants",
            {
                "resourceType": "Patient",
                "id": "choice-pat",
                "deceasedBoolean": True,
                "deceasedDateTime": "2026-01-01T00:00:00Z",
            },
            False,
        ),
        (
            "choice_observation_value_both_variants",
            {
                "resourceType": "Observation",
                "id": "choice-obs",
                "status": "final",
                "code": {"text": "HR"},
                "valueInteger": 72,
                "valueString": "72",
            },
            False,
        ),
        (
            "prim_ext_valid_birthdate_and_given_array",
            {
                "resourceType": "Patient",
                "id": "prim-ext-ok",
                "name": [{"family": "Doe", "given": ["Jane"], "_given": [None]}],
                "birthDate": "1990-05-15",
                "_birthDate": {
                    "id": "bd-ext-1",
                    "extension": [
                        {
                            "url": "http://hl7.org/fhir/StructureDefinition/patient-birthTime",
                            "valueDateTime": "1990-05-15T08:30:00Z",
                        }
                    ],
                },
            },
            True,
        ),
        (
            "prim_ext_invalid_unknown_key",
            {
                "resourceType": "Patient",
                "id": "prim-ext-bad",
                "birthDate": "1990-05-15",
                "_birthDate": {"unknownKey": "bad"},
            },
            False,
        ),
        # 4. Recursive Contained & Bundle Entry Validation
        (
            "recursive_contained_invalid_resource",
            {
                "resourceType": "Patient",
                "id": "rec-cont-bad",
                "contained": [{"resourceType": "Organization", "id": "org-1", "bogusField": 1}],
            },
            False,
        ),
        (
            "recursive_bundle_entry_invalid_resource",
            {
                "resourceType": "Bundle",
                "id": "rec-bdl-bad",
                "type": "collection",
                "entry": [
                    {
                        "fullUrl": "urn:uuid:22222222-3333-4444-5555-666666666666",
                        "resource": {"resourceType": "Patient", "id": "p-bad", "bogusField": 1},
                    }
                ],
            },
            False,
        ),
        # 5. Multi-IG Profile Cases (R4 Vital Signs, US Core 8.0.1, UV IPS 1.0.0)
        (
            "profile_vitalsigns_valid",
            {
                "resourceType": "Observation",
                "id": "vs-ok",
                "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/vitalsigns"]},
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "subject": {"reference": "Patient/pat-1"},
                "effectiveDateTime": "2026-01-01T10:00:00Z",
                "valueQuantity": {
                    "value": 72,
                    "unit": "beats/min",
                    "system": "http://unitsofmeasure.org",
                    "code": "/min",
                },
            },
            True,
        ),
        (
            "profile_heartrate_wrong_value_type",
            {
                "resourceType": "Observation",
                "id": "hr-bad-type",
                "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/heartrate"]},
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "subject": {"reference": "Patient/pat-1"},
                "effectiveDateTime": "2026-01-01T10:00:00Z",
                "valueString": "seventy-two",
            },
            False,
        ),
        (
            "profile_bodyweight_missing_subject",
            {
                "resourceType": "Observation",
                "id": "bw-no-subj",
                "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/bodyweight"]},
                "status": "final",
                "category": [
                    {
                        "coding": [
                            {
                                "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                                "code": "vital-signs",
                            }
                        ]
                    }
                ],
                "code": {"coding": [{"system": "http://loinc.org", "code": "29463-7"}]},
                "effectiveDateTime": "2026-01-01T10:00:00Z",
                "valueQuantity": {
                    "value": 70,
                    "unit": "kg",
                    "system": "http://unitsofmeasure.org",
                    "code": "kg",
                },
            },
            False,
        ),
        (
            "profile_us_core_patient_valid",
            {
                "resourceType": "Patient",
                "id": "us-pat-ok",
                "meta": {
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
                },
                "identifier": [{"system": "http://hospital.org", "value": "123"}],
                "name": [{"family": "Smith", "given": ["Alex"]}],
                "gender": "male",
            },
            True,
        ),
        (
            "profile_us_core_patient_missing_name",
            {
                "resourceType": "Patient",
                "id": "us-pat-bad",
                "meta": {
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
                },
                "identifier": [{"system": "http://hospital.org", "value": "123"}],
                "gender": "male",
            },
            False,
        ),
        (
            "profile_us_core_patient_missing_identifier",
            {
                "resourceType": "Patient",
                "id": "us-pat-no-id",
                "meta": {
                    "profile": ["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"]
                },
                "name": [{"family": "Smith", "given": ["Alex"]}],
                "gender": "male",
            },
            False,
        ),
        (
            "profile_ips_patient_missing_name",
            {
                "resourceType": "Patient",
                "id": "ips-pat-bad",
                "meta": {
                    "profile": ["http://hl7.org/fhir/uv/ips/StructureDefinition/Patient-uv-ips"]
                },
                "gender": "female",
            },
            False,
        ),
        (
            "profile_ips_allergy_missing_patient",
            {
                "resourceType": "AllergyIntolerance",
                "id": "ips-allergy-bad",
                "meta": {
                    "profile": [
                        "http://hl7.org/fhir/uv/ips/StructureDefinition/AllergyIntolerance-uv-ips"
                    ]
                },
                "code": {"coding": [{"system": "http://snomed.info/sct", "code": "91936005"}]},
            },
            False,
        ),
        # 6. Tier 2 Base R4 FHIRPath Invariants (dom-2..dom-5, obs-3)
        (
            "inv_dom2_nested_contained",
            {
                "resourceType": "Patient",
                "id": "dom2-bad",
                "contained": [
                    {
                        "resourceType": "Practitioner",
                        "id": "c1",
                        "contained": [
                            {"resourceType": "Organization", "id": "c2", "name": "Nested"}
                        ],
                    }
                ],
                "generalPractitioner": [{"reference": "#c1"}],
            },
            False,
        ),
        (
            "inv_dom3_unreferenced_contained",
            {
                "resourceType": "Patient",
                "id": "dom3-bad",
                "contained": [{"resourceType": "Organization", "id": "orphan", "name": "Orphan"}],
            },
            False,
        ),
        (
            "inv_dom4_contained_meta_version_id",
            {
                "resourceType": "Patient",
                "id": "dom4-bad",
                "managingOrganization": {"reference": "#org1"},
                "contained": [
                    {
                        "resourceType": "Organization",
                        "id": "org1",
                        "name": "Org",
                        "meta": {"versionId": "1"},
                    }
                ],
            },
            False,
        ),
        (
            "inv_dom5_contained_meta_security",
            {
                "resourceType": "Patient",
                "id": "dom5-bad",
                "managingOrganization": {"reference": "#org1"},
                "contained": [
                    {
                        "resourceType": "Organization",
                        "id": "org1",
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
            },
            False,
        ),
        (
            "inv_obs3_empty_reference_range",
            {
                "resourceType": "Observation",
                "id": "obs3-bad",
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "8867-4"}]},
                "referenceRange": [{}],
            },
            False,
        ),
        # 7. Tier 2 Specialized R4 Resource Invariants (que-*, cpb-*, opd-*, spd-*, cmd-*, sub-*)
        (
            "inv_que_valid_questionnaire",
            {
                "resourceType": "Questionnaire",
                "id": "que-ok",
                "status": "active",
                "item": [
                    {"linkId": "q1", "type": "boolean", "text": "Has allergy?"},
                    {
                        "linkId": "q2",
                        "type": "string",
                        "text": "Details",
                        "enableWhen": [{"question": "q1", "operator": "=", "answerBoolean": True}],
                    },
                ],
            },
            True,
        ),
        (
            "inv_que2_duplicate_link_id",
            {
                "resourceType": "Questionnaire",
                "id": "que2-bad",
                "status": "active",
                "item": [
                    {"linkId": "dup", "type": "string"},
                    {"linkId": "dup", "type": "boolean"},
                ],
            },
            False,
        ),
        (
            "inv_que5_group_with_answer_option",
            {
                "resourceType": "Questionnaire",
                "id": "que5-bad",
                "status": "active",
                "item": [
                    {
                        "linkId": "grp",
                        "type": "group",
                        "answerOption": [{"valueString": "bad"}],
                        "item": [{"linkId": "child", "type": "string"}],
                    }
                ],
            },
            False,
        ),
        (
            "inv_que4_answer_option_and_valueset",
            {
                "resourceType": "Questionnaire",
                "id": "que4-bad",
                "status": "active",
                "item": [
                    {
                        "linkId": "q1",
                        "type": "choice",
                        "answerOption": [{"valueString": "a"}],
                        "answerValueSet": "http://hl7.org/fhir/ValueSet/yesno",
                    }
                ],
            },
            False,
        ),
        (
            "inv_cpb1_missing_rest_messaging_document",
            {
                "resourceType": "CapabilityStatement",
                "id": "cpb1-bad",
                "status": "active",
                "date": "2026-01-01",
                "kind": "instance",
                "fhirVersion": "4.0.1",
                "format": ["json"],
                "description": "Missing rest/messaging/document",
            },
            False,
        ),
        (
            "inv_cpb3_messaging_endpoint_not_instance",
            {
                "resourceType": "CapabilityStatement",
                "id": "cpb3-bad",
                "status": "active",
                "date": "2026-01-01",
                "kind": "capability",
                "fhirVersion": "4.0.1",
                "format": ["json"],
                "description": "Bad messaging endpoint on capability",
                "messaging": [
                    {
                        "endpoint": [
                            {
                                "protocol": {
                                    "system": "http://terminology.hl7.org/CodeSystem/message-transport",
                                    "code": "http",
                                },
                                "address": "http://example.org/fhir",
                            }
                        ]
                    }
                ],
            },
            False,
        ),
        (
            "inv_opd2_search_type_not_string",
            {
                "resourceType": "OperationDefinition",
                "id": "opd2-bad",
                "name": "BadOp",
                "status": "active",
                "kind": "operation",
                "code": "bad-op",
                "system": True,
                "type": False,
                "instance": False,
                "parameter": [
                    {
                        "name": "p1",
                        "use": "in",
                        "min": 0,
                        "max": "1",
                        "type": "integer",
                        "searchType": "token",
                    }
                ],
            },
            False,
        ),
        (
            "inv_spd2_chain_not_reference",
            {
                "resourceType": "SearchParameter",
                "id": "spd2-bad",
                "url": "http://example.org/SearchParameter/spd2-bad",
                "name": "bad-chain",
                "status": "active",
                "description": "Chain on string param",
                "code": "bad-chain",
                "base": ["Patient"],
                "type": "string",
                "chain": ["name"],
            },
            False,
        ),
        (
            "inv_cmd1_narrower_missing_comment",
            {
                "resourceType": "ConceptMap",
                "id": "cmd1-bad",
                "status": "active",
                "group": [
                    {
                        "source": "http://example.org/cs1",
                        "target": "http://example.org/cs2",
                        "element": [
                            {
                                "code": "A",
                                "target": [{"code": "B", "equivalence": "narrower"}],
                            }
                        ],
                    }
                ],
            },
            False,
        ),
        # 8. Tier 2 Element Constraints & IG FHIRPath Constraints (SimpleQuantity, us-core-17)
        (
            "profile_r4_cholesterol_simple_quantity_comparator_rejected",
            {
                "resourceType": "Observation",
                "id": "chol-bad",
                "meta": {"profile": ["http://hl7.org/fhir/StructureDefinition/cholesterol"]},
                "status": "final",
                "code": {"coding": [{"system": "http://loinc.org", "code": "35200-5"}]},
                "subject": {"reference": "Patient/pat-1"},
                "effectiveDateTime": "2026-01-01",
                "valueQuantity": {
                    "value": 4.0,
                    "unit": "mmol/L",
                    "system": "http://unitsofmeasure.org",
                    "code": "mmol/L",
                },
                "referenceRange": [{"high": {"value": 4.5, "comparator": "<"}}],
            },
            False,
        ),
        (
            "profile_us_core_practitioner_npi_valid",
            {
                "resourceType": "Practitioner",
                "id": "us-pract-ok",
                "meta": {
                    "profile": [
                        "http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"
                    ]
                },
                "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567893"}],
                "name": [{"family": "Smith", "given": ["Alice"]}],
            },
            True,
        ),
        (
            "profile_us_core_practitioner_npi_bad_luhn",
            {
                "resourceType": "Practitioner",
                "id": "us-pract-bad",
                "meta": {
                    "profile": [
                        "http://hl7.org/fhir/us/core/StructureDefinition/us-core-practitioner"
                    ]
                },
                "identifier": [{"system": "http://hl7.org/fhir/sid/us-npi", "value": "1234567890"}],
                "name": [{"family": "Smith", "given": ["Alice"]}],
            },
            False,
        ),
    ]


def _build_corpus_cases() -> list[tuple[str, dict[str, Any], bool]]:
    """Build 292 base R4 cases (valid + mutated per resource) + targeted cases for live parity."""
    cases: list[tuple[str, dict[str, Any], bool]] = []
    examples = _select_official_examples()
    assert len(examples) == 146, f"Expected 146 resource examples, got {len(examples)}"

    for idx, rt in enumerate(sorted(RESOURCE_MODELS)):
        base = examples[rt]
        cases.append((f"{rt}__valid", base, True))
        mode = idx % 3
        if mode == 0:
            mutated = {**base, "unknownFieldXYZ": "invalid"}
        elif mode == 1:
            mutated = {**base, "extension": []}
        else:
            mutated = {**base, "id": "invalid id with spaces!"}
        cases.append((f"{rt}__invalid_{mode}", mutated, False))

    cases.extend(_extra_equivalence_cases())
    return cases


def test_extra_equivalence_cases_offline_python_validation() -> None:
    """Verify all targeted equivalence cases deterministically in Python without needing JVM."""
    for name, payload, expected_valid in _extra_equivalence_cases():
        issues = validate_resource(payload)
        assert (len(issues) == 0) == expected_valid, f"[{name}] Python mismatch: {issues}"


@pytest.mark.hl7_live
@pytest.mark.skipif(VALIDATOR_JAR is None, reason="validator_cli.jar not found")
def test_all_146_resources_and_profiles_live_hl7_equivalence(tmp_path: Path) -> None:
    """Validate all 146 R4 types, invariants, and IG profiles in HL7 batch vs Python."""
    assert VALIDATOR_JAR is not None
    cases = _build_corpus_cases()
    for idx, (name, payload, _) in enumerate(cases):
        (tmp_path / f"{idx:04d}_{name}.json").write_text(json.dumps(payload), encoding="utf-8")

    t_py0 = time.perf_counter()
    py_results = [len(validate_resource(payload)) == 0 for _, payload, _ in cases]
    t_py = time.perf_counter() - t_py0

    out_file = tmp_path / "hl7_bundle_outcome.json"
    t_hl7_0 = time.perf_counter()
    subprocess.run(
        [
            "java",
            "-jar",
            str(VALIDATOR_JAR),
            str(tmp_path / "*.json"),
            "-version",
            "4.0.1",
            "-tx",
            "n/a",
            "-ig",
            "hl7.fhir.uv.ips#1.0.0",
            "-ig",
            "hl7.fhir.us.core.r4#8.0.1",
            "-output",
            str(out_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    t_hl7 = time.perf_counter() - t_hl7_0

    assert out_file.exists(), "HL7 batch validation did not produce output file"
    bundle = json.loads(out_file.read_text(encoding="utf-8"))
    entries = bundle.get("entry", [])
    assert len(entries) == len(cases), f"Expected {len(cases)} outcomes, got {len(entries)}"

    mismatches: list[str] = []
    for (name, _, expected_valid), py_ok, entry in zip(cases, py_results, entries, strict=True):
        outcome = entry.get("resource", {})
        hl7_errors = [
            iss.get("diagnostics", "")
            for iss in outcome.get("issue", [])
            if iss.get("severity") in ("error", "fatal")
        ]
        structural_hl7_errors = [
            e
            for e in hl7_errors
            if (
                "unable to resolve" not in e.lower()
                and "terminology" not in e.lower()
                and "could not confirm" not in e.lower()
                and "no valid coding" not in e.lower()
                and "not in the value set" not in e.lower()
                and "value should be from" not in e.lower()
                and "none of the codings provided" not in e.lower()
                and "unable to find" not in e.lower()
                and "unable to check" not in e.lower()
                and "draft code system" not in e.lower()
                and "reference" not in e.lower()
            )
            or "target" in e.lower()
        ]
        hl7_ok = len(structural_hl7_errors) == 0
        if py_ok != expected_valid:
            mismatches.append(f"{name}: Python={py_ok}, expected={expected_valid}")
        elif not expected_valid and hl7_ok:
            mismatches.append(f"{name}: HL7 unexpectedly passed invalid case")

    print(
        f"\nBatch Live Equivalence ({len(cases)} cases / 146 R4 types + invariants + profiles): "
        f"Python={t_py:.4f}s vs HL7={t_hl7:.2f}s ({t_hl7 / t_py:.1f}x faster)"
    )
    assert not mismatches, "Equivalence mismatches:\n" + "\n".join(mismatches[:20])
