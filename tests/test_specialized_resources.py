"""Tests for specialized FHIR R4 resource invariants and Questionnaire/Response semantics."""

from __future__ import annotations

from typing import Any

import pytest

from fhirlance.questionnaire import (
    validate_questionnaire_response_against_questionnaire,
    validate_questionnaire_semantics,
)
from fhirlance.resource_validator import validate_resource
from fhirlance.terminology import TxOptions


def _has_issue(issues: list[str], needle: str) -> bool:
    return any(needle in issue for issue in issues)


# ---------------------------------------------------------------------------
# Questionnaire (que-1..que-13 + semantic checks)
# ---------------------------------------------------------------------------


def test_questionnaire_valid() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            {
                "linkId": "grp1",
                "type": "group",
                "text": "Group 1",
                "item": [
                    {
                        "linkId": "q1",
                        "type": "boolean",
                        "text": "Do you have symptoms?",
                    },
                    {
                        "linkId": "q2",
                        "type": "string",
                        "text": "Describe symptoms",
                        "enableWhen": [
                            {"question": "q1", "operator": "=", "answerBoolean": True},
                        ],
                    },
                ],
            }
        ],
    }
    assert validate_resource(q, tx="off") == []


@pytest.mark.parametrize(
    ("item", "expected"),
    [
        ({"linkId": "g", "type": "group"}, "Invariant[que-1]"),
        ({"linkId": "d", "type": "display", "item": [{"linkId": "x", "type": "string"}]}, "que-1"),
        (
            {"linkId": "d", "type": "display", "code": [{"system": "http://s", "code": "c"}]},
            "Invariant[que-3]",
        ),
        ({"linkId": "d", "type": "display", "required": True}, "Invariant[que-6]"),
        ({"linkId": "d", "type": "display", "repeats": True}, "Invariant[que-6]"),
        ({"linkId": "d", "type": "display", "readOnly": True}, "Invariant[que-9]"),
        (
            {"linkId": "d", "type": "display", "initial": [{"valueString": "hi"}]},
            "Invariant[que-8]",
        ),
        (
            {
                "linkId": "g",
                "type": "group",
                "initial": [{"valueString": "hi"}],
                "item": [{"linkId": "c", "type": "string"}],
            },
            "Invariant[que-8]",
        ),
        (
            {
                "linkId": "q",
                "type": "choice",
                "answerOption": [{"valueString": "A"}],
                "answerValueSet": "http://example.org/vs",
            },
            "Invariant[que-4]",
        ),
        (
            {
                "linkId": "q",
                "type": "boolean",
                "answerOption": [{"valueBoolean": True}],
            },
            "Invariant[que-5]",
        ),
        (
            {"linkId": "q", "type": "date", "maxLength": 10},
            "Invariant[que-10]",
        ),
        (
            {
                "linkId": "q",
                "type": "choice",
                "answerOption": [{"valueString": "A"}],
                "initial": [{"valueString": "A"}],
            },
            "Invariant[que-11]",
        ),
        (
            {
                "linkId": "q",
                "type": "string",
                "enableWhen": [
                    {"question": "a", "operator": "exists", "answerBoolean": True},
                    {"question": "b", "operator": "exists", "answerBoolean": True},
                    {"question": "c", "operator": "exists", "answerBoolean": True},
                ],
            },
            "Invariant[que-12]",
        ),
        (
            {
                "linkId": "q",
                "type": "string",
                "repeats": False,
                "initial": [{"valueString": "a"}, {"valueString": "b"}],
            },
            "Invariant[que-13]",
        ),
        (
            {
                "linkId": "q",
                "type": "string",
                "enableWhen": [{"question": "other", "operator": "exists"}],
            },
            "Invariant[que-7]",
        ),
    ],
)
def test_questionnaire_item_invariants(item: dict[str, Any], expected: str) -> None:
    q: dict[str, Any] = {"resourceType": "Questionnaire", "status": "active", "item": [item]}
    issues = validate_resource(q, tx="off")
    assert _has_issue(issues, expected), f"Expected {expected} in {issues}"


def test_questionnaire_duplicate_link_id_nested() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            {
                "linkId": "dup",
                "type": "group",
                "item": [{"linkId": "dup", "type": "string"}],
            }
        ],
    }
    issues = validate_resource(q, tx="off")
    assert _has_issue(issues, "Invariant[que-2]")


def test_questionnaire_enable_when_semantics_and_valueset_warning() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            {"linkId": "q1", "type": "boolean"},
            {
                "linkId": "q2",
                "type": "choice",
                "answerValueSet": "http://example.org/ValueSet/unknown|1.0",
                "enableWhen": [
                    {"question": "missing", "operator": "=", "answerString": "x"},
                    {"question": "q1", "operator": "=", "answerString": "yes"},
                    {"question": "q1", "operator": "exists", "answerBoolean": True},
                ],
                "enableBehavior": "any",
            },
        ],
    }
    warnings: list[str] = []
    issues = validate_resource(q, tx="local", _warnings_out=warnings)
    assert _has_issue(issues, "does not reference a linkId")
    assert _has_issue(issues, "incompatible with question 'q1' type 'boolean'")
    assert any("unknown|1.0" in w for w in warnings)

    # Direct semantic call with tx_options=None
    direct_errors = validate_questionnaire_semantics(q, tx_options=None, warnings_out=None)
    assert len(direct_errors) == 2


# ---------------------------------------------------------------------------
# QuestionnaireResponse (qrs-1 + cross-resource validation)
# ---------------------------------------------------------------------------


def test_questionnaire_response_qrs1_nested_and_answer_item() -> None:
    qr_invalid: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [
            {
                "linkId": "q1",
                "answer": [{"valueString": "ok", "item": [{"linkId": "sub"}]}],
                "item": [{"linkId": "sub2"}],
            }
        ],
    }
    issues = validate_resource(qr_invalid, tx="off")
    assert _has_issue(issues, "Invariant[qrs-1]")

    # Valid answer.item without sibling item
    qr_valid: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [
            {
                "linkId": "q1",
                "answer": [
                    {
                        "valueString": "ok",
                        "item": [{"linkId": "sub", "answer": [{"valueBoolean": True}]}],
                    }
                ],
            }
        ],
    }
    assert validate_resource(qr_valid, tx="off") == []


def test_questionnaire_response_cross_validation_checks() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "url": "http://example.org/Questionnaire/sample",
        "version": "1.0",
        "status": "active",
        "item": [
            {"linkId": "trigger", "type": "integer", "required": True},
            {
                "linkId": "cond_req",
                "type": "string",
                "required": True,
                "enableWhen": [{"question": "trigger", "operator": ">", "answerInteger": 5}],
            },
            {
                "linkId": "disabled_req",
                "type": "string",
                "required": True,
                "enableWhen": [{"question": "trigger", "operator": "<", "answerInteger": 0}],
            },
            {
                "linkId": "opt_choice",
                "type": "choice",
                "answerOption": [
                    {"valueCoding": {"system": "http://sys", "code": "A"}},
                    {"valueString": "B"},
                ],
            },
            {
                "linkId": "vs_choice",
                "type": "choice",
                "answerValueSet": "http://hl7.org/fhir/ValueSet/administrative-gender",
            },
            {"linkId": "single_int", "type": "integer", "repeats": False},
        ],
    }

    qr: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "questionnaire": "http://example.org/Questionnaire/sample|1.0",
        "status": "completed",
        "item": [
            {"linkId": "trigger", "answer": [{"valueInteger": 10}]},
            {"linkId": "unknown_link", "answer": [{"valueString": "x"}]},
            {
                "linkId": "opt_choice",
                "answer": [{"valueCoding": {"system": "http://sys", "code": "WRONG"}}],
            },
            {"linkId": "vs_choice", "answer": [{"valueCoding": {"code": "not-a-gender"}}]},
            {
                "linkId": "single_int",
                "answer": [{"valueString": "bad-type"}, {"valueInteger": 2}],
            },
        ],
    }

    issues = validate_resource(qr, questionnaire_resource=q, tx="local")
    assert _has_issue(issues, "linkId 'unknown_link' does not exist in Questionnaire")
    assert _has_issue(issues, "does not match any allowed answerOption")
    assert _has_issue(
        issues, "value type 'valueString' is incompatible with Questionnaire item type"
    )
    assert _has_issue(issues, "does not allow repeating answers")
    assert _has_issue(issues, "required Questionnaire item 'cond_req' is missing")
    assert not _has_issue(issues, "disabled_req")
    assert _has_issue(issues, "not-a-gender")


def test_questionnaire_response_resolution_bundle_and_contained() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "id": "q-contained",
        "url": "http://example.org/Questionnaire/q-bundle",
        "status": "active",
        "item": [{"linkId": "q1", "type": "boolean", "required": True}],
    }

    # 1. Contained #id resolution
    qr_contained: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "contained": [q],
        "questionnaire": "#q-contained",
        "status": "completed",
    }
    issues_contained = validate_resource(qr_contained, tx="off")
    assert _has_issue(issues_contained, "required Questionnaire item 'q1' is missing")

    # 2. Bundle resolution by canonical url
    bundle: dict[str, Any] = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {"fullUrl": "http://example.org/Questionnaire/q-bundle", "resource": q},
            {
                "fullUrl": "http://example.org/QuestionnaireResponse/qr1",
                "resource": {
                    "resourceType": "QuestionnaireResponse",
                    "questionnaire": "http://example.org/Questionnaire/q-bundle|1.0",
                    "status": "completed",
                },
            },
        ],
    }
    issues_bundle = validate_resource(bundle, tx="off")
    assert _has_issue(issues_bundle, "required Questionnaire item 'q1' is missing")


def test_questionnaire_response_enable_when_operators() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            {"linkId": "num", "type": "decimal"},
            {"linkId": "txt", "type": "string"},
            {
                "linkId": "any_target",
                "type": "string",
                "required": True,
                "enableBehavior": "any",
                "enableWhen": [
                    {"question": "num", "operator": ">=", "answerDecimal": 2.5},
                    {"question": "txt", "operator": "!=", "answerString": "skip"},
                ],
            },
            {
                "linkId": "exists_false_target",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "missing_q", "operator": "exists", "answerBoolean": False}
                ],
            },
        ],
    }
    qr: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [{"linkId": "num", "answer": [{"valueDecimal": 3.0}]}],
    }
    issues = validate_questionnaire_response_against_questionnaire(
        qr, q, tx_options=TxOptions(mode="off")
    )
    assert _has_issue(issues, "any_target")
    assert _has_issue(issues, "exists_false_target")


# ---------------------------------------------------------------------------
# CapabilityStatement (cpb-1, cpb-2, cpb-3, cpb-7, cpb-9, cpb-12, cpb-14..16)
# ---------------------------------------------------------------------------


def test_capability_statement_invariants() -> None:
    base: dict[str, Any] = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-01-01",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
    }
    # cpb-1 (no rest/messaging/document), cpb-2 (no description/software/impl),
    # cpb-14 (instance needs impl)
    issues = validate_resource(base, tx="off")
    assert _has_issue(issues, "Invariant[cpb-1]")
    assert _has_issue(issues, "Invariant[cpb-2]")
    assert _has_issue(issues, "Invariant[cpb-14]")

    # cpb-3 (messaging.endpoint when kind != instance), cpb-7 (dup document), cpb-9 (dup resource),
    # cpb-12 (dup searchParam), cpb-15 (capability needs software & forbids impl)
    cap_bad: dict[str, Any] = {
        **base,
        "kind": "capability",
        "description": "Test",
        "implementation": {"description": "Impl"},
        "messaging": [{"endpoint": [{"protocol": {"code": "http"}, "address": "http://ex.org"}]}],
        "document": [
            {"mode": "producer", "profile": "http://ex.org/p1"},
            {"mode": "producer", "profile": "http://ex.org/p1"},
        ],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "searchParam": [
                            {"name": "name", "type": "string"},
                            {"name": "name", "type": "string"},
                        ],
                    },
                    {"type": "Patient"},
                ],
            }
        ],
    }
    issues_cap = validate_resource(cap_bad, tx="off")
    for code in ("cpb-3", "cpb-7", "cpb-9", "cpb-12", "cpb-15"):
        assert _has_issue(issues_cap, f"Invariant[{code}]"), f"Missing {code} in {issues_cap}"

    # cpb-16 (requirements forbids impl and software)
    req_bad: dict[str, Any] = {
        **base,
        "kind": "requirements",
        "description": "Reqs",
        "software": {"name": "Sw"},
        "rest": [{"mode": "server"}],
    }
    assert _has_issue(validate_resource(req_bad, tx="off"), "Invariant[cpb-16]")


# ---------------------------------------------------------------------------
# OperationDefinition (opd-1..3), SearchParameter (spd-1..2), ConceptMap (cmd-1..3)
# ---------------------------------------------------------------------------


def test_operation_definition_invariants() -> None:
    od: dict[str, Any] = {
        "resourceType": "OperationDefinition",
        "name": "test-op",
        "status": "active",
        "kind": "operation",
        "code": "test",
        "system": True,
        "type": False,
        "instance": False,
        "parameter": [
            {"name": "p1", "use": "in", "min": 0, "max": "1"},
            {
                "name": "p2",
                "use": "in",
                "min": 0,
                "max": "1",
                "type": "integer",
                "searchType": "number",
                "targetProfile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
            },
        ],
    }
    issues = validate_resource(od, tx="off")
    for code in ("opd-1", "opd-2", "opd-3"):
        assert _has_issue(issues, f"Invariant[{code}]")


def test_search_parameter_invariants() -> None:
    sp: dict[str, Any] = {
        "resourceType": "SearchParameter",
        "url": "http://example.org/sp",
        "name": "test-sp",
        "status": "active",
        "description": "desc",
        "code": "test",
        "base": ["Patient"],
        "type": "string",
        "xpath": "f:Patient/f:name",
        "chain": ["name"],
    }
    issues = validate_resource(sp, tx="off")
    assert _has_issue(issues, "Invariant[spd-1]")
    assert _has_issue(issues, "Invariant[spd-2]")


def test_concept_map_invariants() -> None:
    cm: dict[str, Any] = {
        "resourceType": "ConceptMap",
        "status": "active",
        "group": [
            {
                "element": [
                    {
                        "code": "a",
                        "target": [{"code": "b", "equivalence": "narrower"}],
                    }
                ],
                "unmapped": {"mode": "fixed"},
            },
            {
                "unmapped": {"mode": "other-map"},
            },
        ],
    }
    issues = validate_resource(cm, tx="off")
    for code in ("cmd-1", "cmd-2", "cmd-3"):
        assert _has_issue(issues, f"Invariant[{code}]")


# ---------------------------------------------------------------------------
# TestScript (tst-1..13), StructureMap (smp-1..2), MolecularSequence (msq-3,5,6)
# ---------------------------------------------------------------------------


def test_testscript_invariants() -> None:
    ts: dict[str, Any] = {
        "resourceType": "TestScript",
        "url": "http://example.org/ts",
        "name": "ts",
        "status": "active",
        "metadata": {"capability": [{"description": "cap"}]},
        "variable": [{"name": "v1", "expression": "a", "headerField": "b", "path": "c"}],
        "setup": {
            "action": [
                {"operation": {"type": {"code": "read"}}, "assert": {"response": "okay"}},
                {
                    "operation": {"type": {"code": "read"}},
                },
                {
                    "assert": {
                        "response": "okay",
                        "path": "x",
                        "compareToSourceId": "s1",
                        "direction": "request",
                    }
                },
            ]
        },
        "test": [
            {
                "action": [
                    {},
                    {"operation": {"type": {"code": "update"}, "targetId": "r1", "url": "/x"}},
                    {
                        "assert": {
                            "responseCode": "200",
                            "path": "x",
                            "compareToSourceExpression": "y",
                            "direction": "request",
                        }
                    },
                ]
            }
        ],
        "teardown": {"action": [{"operation": {"type": {"code": "delete"}}}]},
    }
    issues = validate_resource(ts, tx="off")
    for num in range(1, 14):
        assert _has_issue(issues, f"Invariant[tst-{num}]"), f"Missing tst-{num} in {issues}"


def test_structure_map_invariants() -> None:
    sm: dict[str, Any] = {
        "resourceType": "StructureMap",
        "url": "http://example.org/sm",
        "name": "sm",
        "status": "active",
        "structure": [{"url": "http://hl7.org/fhir/StructureDefinition/Patient", "mode": "source"}],
        "group": [
            {
                "name": "g1",
                "typeMode": "none",
                "input": [{"name": "src", "mode": "source"}],
                "rule": [
                    {
                        "name": "r1",
                        "source": [{"context": "src"}],
                        "target": [{"element": "name"}],
                        "rule": [
                            {
                                "name": "r2",
                                "source": [{"context": "src"}],
                                "target": [{"context": "tgt"}],
                            }
                        ],
                    }
                ],
            }
        ],
    }
    issues = validate_resource(sm, tx="off")
    assert _has_issue(issues, "Invariant[smp-1]")
    assert _has_issue(issues, "Invariant[smp-2]")


def test_molecular_sequence_invariants() -> None:
    ms: dict[str, Any] = {
        "resourceType": "MolecularSequence",
        "coordinateSystem": 2,
        "referenceSeq": {
            "chromosome": {"coding": [{"code": "1"}]},
            "genomeBuild": "GRCh38",
            "referenceSeqString": "ACGT",
        },
    }
    issues = validate_resource(ms, tx="off")
    assert _has_issue(issues, "Invariant[msq-3]")
    assert _has_issue(issues, "Invariant[msq-6]")

    ms_chr_only: dict[str, Any] = {
        "resourceType": "MolecularSequence",
        "coordinateSystem": 0,
        "referenceSeq": {
            "chromosome": {"coding": [{"code": "1"}]},
        },
    }
    issues_chr = validate_resource(ms_chr_only, tx="off")
    assert _has_issue(issues_chr, "Invariant[msq-5]")
    assert _has_issue(issues_chr, "Invariant[msq-6]")


# ---------------------------------------------------------------------------
# Subscription (rest-hook, email, R5-backport extensions)
# ---------------------------------------------------------------------------


def test_subscription_invariants() -> None:
    sub_rest_bad: dict[str, Any] = {
        "resourceType": "Subscription",
        "status": "requested",
        "reason": "test",
        "criteria": "Patient",
        "extension": [
            {
                "url": (
                    "http://hl7.org/fhir/uv/subscriptions-backport/"
                    "StructureDefinition/backport-topic-canonical"
                ),
                "valueUri": "   ",
            }
        ],
        "channel": {
            "type": "rest-hook",
            "endpoint": "ftp://invalid.example.org",
            "extension": [
                {
                    "url": (
                        "http://hl7.org/fhir/uv/subscriptions-backport/"
                        "StructureDefinition/backport-payload-content"
                    ),
                    "valueCode": "invalid-code",
                }
            ],
        },
    }
    issues_rest = validate_resource(sub_rest_bad, tx="off")
    assert _has_issue(issues_rest, "rest-hook endpoint must start with http:// or https://")
    assert _has_issue(issues_rest, "backport-topic-canonical requires non-empty")
    assert _has_issue(issues_rest, "backport-payload-content valueCode must be")

    sub_email_bad: dict[str, Any] = {
        "resourceType": "Subscription",
        "status": "requested",
        "reason": "test",
        "criteria": "Patient",
        "channel": {"type": "email", "endpoint": "not-an-email"},
    }
    assert _has_issue(validate_resource(sub_email_bad, tx="off"), "email endpoint must contain '@'")

    # Valid Subscription cases + backport extensions
    sub_valid: dict[str, Any] = {
        "resourceType": "Subscription",
        "status": "active",
        "reason": "test",
        "criteria": "Patient",
        "extension": [
            {
                "url": (
                    "http://hl7.org/fhir/uv/subscriptions-backport/"
                    "StructureDefinition/backport-topic-canonical"
                ),
                "valueCanonical": "http://example.org/topic",
            }
        ],
        "channel": {
            "type": "rest-hook",
            "endpoint": "https://example.org/hook",
            "extension": [
                {
                    "url": (
                        "http://hl7.org/fhir/uv/subscriptions-backport/"
                        "StructureDefinition/backport-payload-content"
                    ),
                    "valueCode": "full-resource",
                }
            ],
        },
    }
    assert validate_resource(sub_valid, tx="off") == []

    sub_email_ok: dict[str, Any] = {
        "resourceType": "Subscription",
        "status": "active",
        "reason": "test",
        "criteria": "Patient",
        "channel": {"type": "email", "endpoint": "mailto:alerts@example.org"},
    }
    assert validate_resource(sub_email_ok, tx="off") == []


def test_questionnaire_edge_cases_and_comparisons() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            {
                "linkId": "known_vs",
                "type": "choice",
                "answerValueSet": "http://hl7.org/fhir/ValueSet/administrative-gender",
            },
            {
                "linkId": "qty",
                "type": "quantity",
            },
            {
                "linkId": "str_q",
                "type": "string",
            },
            {
                "linkId": "coding_q",
                "type": "choice",
                "answerOption": [
                    {"valueCoding": {"system": "http://sys1", "code": "C1"}},
                    {"valueString": "S1"},
                ],
            },
            {
                "linkId": "req_qty_eq",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "qty", "operator": "=", "answerQuantity": {"value": 10}},
                ],
            },
            {
                "linkId": "req_str_lt",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "str_q", "operator": "<", "answerString": "z"},
                ],
            },
            {
                "linkId": "req_coding_eq",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {
                        "question": "coding_q",
                        "operator": "=",
                        "answerCoding": {"code": "C1"},
                    },
                ],
            },
            {
                "linkId": "req_int_eq",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "coding_q", "operator": "!=", "answerString": "OTHER"},
                ],
            },
        ],
    }
    warnings: list[str] = []
    assert (
        validate_questionnaire_semantics(
            q, tx_options=TxOptions(mode="local"), warnings_out=warnings
        )
        == []
    )
    assert warnings == []

    qr: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [
            {"linkId": "qty", "answer": [{"valueQuantity": {"value": 10}}]},
            {"linkId": "str_q", "answer": [{"valueString": "a"}]},
            {
                "linkId": "coding_q",
                "answer": [{"valueCoding": {"system": "http://sys2", "code": "C1"}}],
            },
        ],
    }
    issues = validate_questionnaire_response_against_questionnaire(
        qr, q, tx_options=TxOptions(mode="local")
    )
    assert _has_issue(issues, "does not match any allowed answerOption")
    assert _has_issue(issues, "req_qty_eq")
    assert _has_issue(issues, "req_str_lt")
    assert _has_issue(issues, "req_coding_eq")
    assert _has_issue(issues, "req_int_eq")


def test_capability_requirements_valid() -> None:
    cap: dict[str, Any] = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-01-01",
        "kind": "requirements",
        "description": "Requirements only",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "rest": [{"mode": "server"}],
    }
    assert validate_resource(cap, tx="off") == []


def test_testscript_tst4_false_flags_and_valid() -> None:
    ts_false_flags: dict[str, Any] = {
        "resourceType": "TestScript",
        "url": "http://example.org/ts-false",
        "name": "ts-false",
        "status": "active",
        "metadata": {"capability": [{"required": False, "validated": False}]},
    }
    issues = validate_resource(ts_false_flags, tx="off")
    assert _has_issue(issues, "Invariant[tst-4]")

    ts_valid: dict[str, Any] = {
        "resourceType": "TestScript",
        "url": "http://example.org/ts-valid",
        "name": "ts-valid",
        "status": "active",
        "metadata": {
            "capability": [
                {
                    "required": True,
                    "validated": False,
                    "capabilities": "http://example.org/CapabilityStatement/1",
                }
            ]
        },
    }
    assert validate_resource(ts_valid, tx="off") == []

    ts_minimal: dict[str, Any] = {
        "resourceType": "TestScript",
        "url": "http://example.org/ts-min",
        "name": "ts-min",
        "status": "active",
        "setup": {
            "action": [
                {
                    "operation": {
                        "type": {"code": "read"},
                        "targetId": "r1",
                        "encodeRequestUrl": True,
                    }
                },
                {"assert": {"response": "okay", "warningOnly": False}},
            ]
        },
        "test": [
            {
                "action": [
                    {
                        "operation": {
                            "type": {"code": "read"},
                            "sourceId": "s1",
                            "encodeRequestUrl": True,
                        }
                    },
                    {
                        "assert": {
                            "path": "id",
                            "operator": "equals",
                            "value": "1",
                            "warningOnly": False,
                        }
                    },
                ]
            }
        ],
    }
    assert validate_resource(ts_minimal, tx="off") == []


def test_questionnaire_deep_recursion_cap() -> None:
    deep_q_item: dict[str, Any] = {"linkId": "leaf", "type": "string", "required": True}
    deep_qr_item: dict[str, Any] = {"linkId": "leaf", "answer": [{"valueString": "ok"}]}
    for idx in range(70):
        deep_q_item = {"linkId": f"g{idx}", "type": "group", "item": [deep_q_item]}
        deep_qr_item = {"linkId": f"g{idx}", "item": [deep_qr_item]}

    q: dict[str, Any] = {"resourceType": "Questionnaire", "status": "active", "item": [deep_q_item]}
    qr: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [deep_qr_item],
    }
    assert validate_questionnaire_semantics(q, tx_options=TxOptions(mode="off")) == []
    assert (
        validate_questionnaire_response_against_questionnaire(
            qr, q, tx_options=TxOptions(mode="off")
        )
        == []
    )


def test_questionnaire_bool_vs_int_and_quantity_ordinal_enable_when() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            {"linkId": "int_q", "type": "integer"},
            {"linkId": "bool_q", "type": "boolean"},
            {"linkId": "qty_q", "type": "quantity"},
            {
                "linkId": "req_bool_vs_int",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "int_q", "operator": "=", "answerBoolean": True},
                ],
            },
            {
                "linkId": "req_false_vs_zero",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "bool_q", "operator": "=", "answerInteger": 0},
                ],
            },
            {
                "linkId": "req_qty_gt",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "qty_q", "operator": ">", "answerQuantity": {"value": 5}},
                ],
            },
            {
                "linkId": "req_qty_le",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "qty_q", "operator": "<=", "answerQuantity": {"value": 10.0}},
                ],
            },
            {
                "linkId": "req_qty_lt_disabled",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "qty_q", "operator": "<", "answerQuantity": {"value": 5}},
                ],
            },
        ],
    }
    qr: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [
            {"linkId": "int_q", "answer": [{"valueInteger": 1}]},
            {"linkId": "bool_q", "answer": [{"valueBoolean": False}]},
            {"linkId": "qty_q", "answer": [{"valueQuantity": {"value": 10, "unit": "kg"}}]},
        ],
    }
    issues = validate_questionnaire_response_against_questionnaire(
        qr, q, tx_options=TxOptions(mode="off")
    )
    assert not _has_issue(issues, "req_bool_vs_int")
    assert not _has_issue(issues, "req_false_vs_zero")
    assert _has_issue(issues, "req_qty_gt")
    assert _has_issue(issues, "req_qty_le")
    assert not _has_issue(issues, "req_qty_lt_disabled")


def test_questionnaire_additional_branch_coverage() -> None:
    q: dict[str, Any] = {
        "resourceType": "Questionnaire",
        "status": "active",
        "item": [
            "not-a-dict",
            {"type": "string"},
            {"linkId": "unknown_type_q", "type": "custom-unknown"},
            {
                "linkId": "opt_str",
                "type": "choice",
                "answerOption": [{"valueString": "B"}],
            },
            {
                "linkId": "unknown_vs_q",
                "type": "choice",
                "answerValueSet": "http://example.org/ValueSet/does-not-exist",
            },
            {
                "linkId": "ew_edge",
                "type": "string",
                "required": True,
                "enableWhen": [
                    "not-a-dict",
                    {"question": "", "operator": "=", "answerString": "x"},
                    {"question": "unknown_type_q", "operator": "=", "answerString": "x"},
                ],
            },
            {
                "linkId": "ew_bad_op",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "opt_str", "operator": "~", "answerString": "B"},
                ],
            },
            {
                "linkId": "ew_no_ans",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "no_such_q", "operator": "=", "answerString": "B"},
                ],
            },
            {
                "linkId": "ew_empty_conds",
                "type": "string",
                "required": True,
                "enableWhen": ["not-a-dict"],
            },
            {
                "linkId": "ew_bad_qty",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"question": "opt_str", "operator": ">", "answerQuantity": {"value": "bad"}},
                ],
            },
            {
                "linkId": "ew_no_q_key",
                "type": "string",
                "required": True,
                "enableWhen": [
                    {"operator": "=", "answerString": "B"},
                ],
            },
        ],
    }
    warnings: list[str] = []
    sem_errors = validate_questionnaire_semantics(
        q, tx_options=TxOptions(mode="local"), warnings_out=warnings
    )
    assert any("no_such_q" in e for e in sem_errors)
    assert any("does-not-exist" in w for w in warnings)

    qr: dict[str, Any] = {
        "resourceType": "QuestionnaireResponse",
        "status": "completed",
        "item": [
            "not-a-dict",
            {"linkId": "opt_str", "answer": [{"valueString": "B"}]},
            {"linkId": "unknown_type_q", "answer": [{"valueString": "ok"}, {"extension": []}]},
            {"linkId": "unknown_vs_q", "answer": [{"valueString": "ok"}]},
            {"linkId": "ew_empty_conds", "answer": []},
        ],
    }
    resp_errors = validate_questionnaire_response_against_questionnaire(
        qr, q, tx_options=TxOptions(mode="local")
    )
    assert _has_issue(resp_errors, "ew_empty_conds")
    assert not _has_issue(resp_errors, "ew_bad_op")
    assert not _has_issue(resp_errors, "ew_no_ans")
    assert not _has_issue(resp_errors, "ew_bad_qty")
    assert not _has_issue(resp_errors, "ew_no_q_key")


def test_specialized_resources_valid_variants() -> None:
    ms_valid: dict[str, Any] = {
        "resourceType": "MolecularSequence",
        "coordinateSystem": 0,
        "referenceSeq": {
            "referenceSeqId": {"coding": [{"code": "NC_000001.11"}]},
            "windowStart": 1,
            "windowEnd": 100,
        },
    }
    assert validate_resource(ms_valid, tx="off") == []

    sm_valid: dict[str, Any] = {
        "resourceType": "StructureMap",
        "url": "http://example.org/sm-ok",
        "name": "sm-ok",
        "status": "active",
        "group": [
            {
                "name": "g1",
                "typeMode": "none",
                "input": [{"name": "src", "mode": "source"}],
                "rule": [
                    {
                        "name": "r1",
                        "source": [{"context": "src"}],
                        "target": [
                            {"context": "tgt", "contextType": "variable", "element": "name"}
                        ],
                    }
                ],
            }
        ],
    }
    assert validate_resource(sm_valid, tx="off") == []

    od_valid: dict[str, Any] = {
        "resourceType": "OperationDefinition",
        "name": "valid-op",
        "status": "active",
        "kind": "operation",
        "code": "valid",
        "system": True,
        "type": False,
        "instance": False,
        "parameter": [
            {
                "name": "p1",
                "use": "in",
                "min": 0,
                "max": "1",
                "type": "Reference",
                "targetProfile": ["http://hl7.org/fhir/StructureDefinition/Patient"],
            }
        ],
    }
    assert validate_resource(od_valid, tx="off") == []

    sp_valid: dict[str, Any] = {
        "resourceType": "SearchParameter",
        "url": "http://example.org/sp-valid",
        "name": "valid-sp",
        "status": "active",
        "description": "desc",
        "code": "valid",
        "base": ["Patient"],
        "type": "reference",
        "expression": "Patient.generalPractitioner",
        "chain": ["name"],
    }
    assert validate_resource(sp_valid, tx="off") == []

    cm_valid: dict[str, Any] = {
        "resourceType": "ConceptMap",
        "status": "active",
        "group": [
            {
                "element": [
                    {
                        "code": "a",
                        "target": [{"code": "b", "equivalence": "equivalent"}],
                    }
                ],
                "unmapped": {"mode": "fixed", "code": "other"},
            },
            {
                "element": [{"code": "b"}],
                "unmapped": {"mode": "other-map", "url": "http://example.org/cm2"},
            },
        ],
    }
    assert validate_resource(cm_valid, tx="off") == []

    cap_instance_valid: dict[str, Any] = {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "date": "2024-01-01",
        "kind": "instance",
        "fhirVersion": "4.0.1",
        "format": ["json"],
        "implementation": {"description": "Impl", "url": "http://example.org/fhir"},
        "messaging": [{"endpoint": [{"protocol": {"code": "http"}, "address": "http://ex.org"}]}],
        "document": [{"mode": "producer", "profile": "http://ex.org/p1"}],
        "rest": [
            {
                "mode": "server",
                "resource": [
                    {
                        "type": "Patient",
                        "searchParam": [{"name": "name", "type": "string"}],
                    }
                ],
            }
        ],
    }
    assert validate_resource(cap_instance_valid, tx="off") == []

    ms_no_refseq: dict[str, Any] = {
        "resourceType": "MolecularSequence",
        "coordinateSystem": 0,
    }
    assert validate_resource(ms_no_refseq, tx="off") == []

    sub_ws: dict[str, Any] = {
        "resourceType": "Subscription",
        "status": "active",
        "reason": "test",
        "criteria": "Patient",
        "extension": [{"url": "http://example.org/other", "valueString": "x"}],
        "channel": {"type": "websocket"},
    }
    assert validate_resource(sub_ws, tx="off") == []

    cm_no_unmapped: dict[str, Any] = {
        "resourceType": "ConceptMap",
        "status": "active",
        "group": [{"element": [{"code": "a"}]}],
    }
    assert validate_resource(cm_no_unmapped, tx="off") == []
