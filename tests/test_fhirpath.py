"""Comprehensive unit tests for the pure-Python FHIRPath R4 engine."""

from __future__ import annotations

import pytest

from fhirlance.fhirpath import (
    EvalContext,
    compile_fhirpath,
    evaluate_fhirpath,
    evaluate_fhirpath_invariant,
)

# ---------------------------------------------------------------------------
# Literals, Variables, Comments, Escapes
# ---------------------------------------------------------------------------


def test_literals_and_escapes() -> None:
    assert evaluate_fhirpath(r"'hello \'world\' \\ \n\t\r\f\u0041'", {}) == [
        "hello 'world' \\ \n\t\r\fA"
    ]
    assert evaluate_fhirpath("42", {}) == [42]
    assert evaluate_fhirpath("3.14", {}) == [3.14]
    assert evaluate_fhirpath("true", {}) == [True]
    assert evaluate_fhirpath("false", {}) == [False]
    assert evaluate_fhirpath("{}", {}) == []
    assert evaluate_fhirpath("@2024-05-01", {}) == ["2024-05-01"]
    assert evaluate_fhirpath("@2024-05-01T10:30:00Z", {}) == ["2024-05-01T10:30:00Z"]
    assert evaluate_fhirpath("`div`", {"div": "<div>hi</div>"}) == ["<div>hi</div>"]


def test_comments_and_variables() -> None:
    expr = """
    // single line comment
    /* multi
       line comment */
    %ucum
    """
    assert evaluate_fhirpath(expr, {}) == ["http://unitsofmeasure.org"]

    patient = {
        "resourceType": "Patient",
        "id": "p1",
        "name": [{"family": "Doe"}, {"family": "Roe"}],
    }
    root = {"resourceType": "Bundle", "id": "b1"}
    assert evaluate_fhirpath("%resource.id", patient, resource=patient, root_resource=root) == [
        "p1"
    ]
    assert evaluate_fhirpath("%rootResource.id", patient, resource=patient, root_resource=root) == [
        "b1"
    ]
    assert evaluate_fhirpath("%context.id", patient) == ["p1"]
    assert evaluate_fhirpath("name.select($this.family & ':' & $index.toString())", patient) == [
        "Doe:0",
        "Roe:1",
    ]


# ---------------------------------------------------------------------------
# Path & Choice Resolution
# ---------------------------------------------------------------------------


def test_path_indexing_and_choice_types() -> None:
    obs = {
        "resourceType": "Observation",
        "valueQuantity": {"value": 98.6, "unit": "degF"},
        "component": [
            {"valueString": "normal"},
            {"valueInteger": 5},
        ],
    }
    assert evaluate_fhirpath("value.value", obs) == [98.6]
    assert evaluate_fhirpath("component[0].value", obs) == ["normal"]
    assert evaluate_fhirpath("component[1].value", obs) == [5]
    assert evaluate_fhirpath("component[99]", obs) == []
    assert evaluate_fhirpath("component['bad']", obs) == []
    assert evaluate_fhirpath("Observation.value.unit", obs) == ["degF"]
    assert evaluate_fhirpath("Patient.value", obs) == []
    assert evaluate_fhirpath("nonexistent.deep", "primitive") == []


# ---------------------------------------------------------------------------
# Operators & Precedence & 3-Valued Logic
# ---------------------------------------------------------------------------


def test_arithmetic_and_string_concat() -> None:
    assert evaluate_fhirpath("1 + 2 * 3", {}) == [7]
    assert evaluate_fhirpath("(1 + 2) * 3", {}) == [9]
    assert evaluate_fhirpath("10 - 3", {}) == [7]
    assert evaluate_fhirpath("7 / 2", {}) == [3.5]
    assert evaluate_fhirpath("7 div 2", {}) == [3]
    assert evaluate_fhirpath("7 mod 2", {}) == [1]
    assert evaluate_fhirpath("7.5 mod 2", {}) == [1.5]
    assert evaluate_fhirpath("5 / 0", {}) == []
    assert evaluate_fhirpath("5 div 0", {}) == []
    assert evaluate_fhirpath("-5 + +2", {}) == [-3]
    assert evaluate_fhirpath("'a' + 'b'", {}) == ["ab"]
    assert evaluate_fhirpath("'a' & {} & 'b'", {}) == ["ab"]
    assert evaluate_fhirpath("1 + {}", {}) == []
    assert evaluate_fhirpath("-'abc'", {}) == []


def test_equality_equivalence_comparison_membership() -> None:
    assert evaluate_fhirpath("1 = 1.0", {}) == [True]
    assert evaluate_fhirpath("1 != true", {}) == [True]
    assert evaluate_fhirpath("1 = {}", {}) == []
    assert evaluate_fhirpath("1 != {}", {}) == []
    assert evaluate_fhirpath("'Hello   World' ~ 'hello world'", {}) == [True]
    assert evaluate_fhirpath("'Hello' !~ 'world'", {}) == [True]
    assert evaluate_fhirpath("{} ~ {}", {}) == [True]
    assert evaluate_fhirpath("{} ~ 1", {}) == [False]
    assert evaluate_fhirpath("2 < 3 and 3 <= 3 and 4 > 3 and 4 >= 4", {}) == [True]
    assert evaluate_fhirpath("@2020-01-01 < @2021-01-01", {}) == [True]
    assert evaluate_fhirpath("2 < 'a'", {}) == []
    assert evaluate_fhirpath("2 in (1 | 2 | 3)", {}) == [True]
    assert evaluate_fhirpath("(1 | 2 | 3) contains 2", {}) == [True]
    assert evaluate_fhirpath("{} in (1 | 2)", {}) == []
    assert evaluate_fhirpath("(1 | 2) contains {}", {}) == []


def test_three_valued_logic_and_precedence() -> None:
    assert evaluate_fhirpath("false and {}", {}) == [False]
    assert evaluate_fhirpath("{} and false", {}) == [False]
    assert evaluate_fhirpath("true and {}", {}) == []
    assert evaluate_fhirpath("true or {}", {}) == [True]
    assert evaluate_fhirpath("{} or true", {}) == [True]
    assert evaluate_fhirpath("false or {}", {}) == []
    assert evaluate_fhirpath("true xor false", {}) == [True]
    assert evaluate_fhirpath("true xor true", {}) == [False]
    assert evaluate_fhirpath("true xor {}", {}) == []
    assert evaluate_fhirpath("false implies false", {}) == [True]
    assert evaluate_fhirpath("{} implies false", {}) == [True]
    assert evaluate_fhirpath("true implies false", {}) == [False]
    assert evaluate_fhirpath("true implies {}", {}) == []
    assert evaluate_fhirpath("false and true or true", {}) == [True]
    assert evaluate_fhirpath("1 | 2 | 2 | 3", {}) == [1, 2, 3]


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


def test_existence_logic_and_filtering_functions() -> None:
    data = {"items": [1, 2, 2, 3], "bools": [True, False]}
    assert evaluate_fhirpath("items.exists()", data) == [True]
    assert evaluate_fhirpath("items.exists($this > 2)", data) == [True]
    assert evaluate_fhirpath("items.empty()", data) == [False]
    assert evaluate_fhirpath("missing.empty()", data) == [True]
    assert evaluate_fhirpath("true.not()", data) == [False]
    assert evaluate_fhirpath("{}.not()", data) == []
    assert evaluate_fhirpath("'x'.hasValue()", data) == [True]
    assert evaluate_fhirpath("items.hasValue()", data) == [False]
    assert evaluate_fhirpath("items.count()", data) == [4]
    assert evaluate_fhirpath("items.distinct()", data) == [1, 2, 3]
    assert evaluate_fhirpath("items.isDistinct()", data) == [False]
    assert evaluate_fhirpath("items.distinct().isDistinct()", data) == [True]
    assert evaluate_fhirpath("bools.allTrue()", data) == [False]
    assert evaluate_fhirpath("bools.anyTrue()", data) == [True]
    assert evaluate_fhirpath("bools.allFalse()", data) == [False]
    assert evaluate_fhirpath("bools.anyFalse()", data) == [True]
    assert evaluate_fhirpath("items.where($this >= 2)", data) == [2, 2, 3]
    assert evaluate_fhirpath("items.all($this > 0)", data) == [True]


def test_repeat_and_subsetting_functions() -> None:
    tree = {
        "id": "root",
        "item": [{"id": "c1", "item": [{"id": "c2"}]}],
    }
    assert evaluate_fhirpath("repeat(item).id", tree) == ["c1", "c2"]
    assert evaluate_fhirpath("(1 | 2 | 3).first()", {}) == [1]
    assert evaluate_fhirpath("(1 | 2 | 3).last()", {}) == [3]
    assert evaluate_fhirpath("(1 | 2 | 3).tail()", {}) == [2, 3]
    assert evaluate_fhirpath("(1 | 2 | 3).skip(1)", {}) == [2, 3]
    assert evaluate_fhirpath("(1 | 2 | 3).take(2)", {}) == [1, 2]
    assert evaluate_fhirpath("(42).single()", {}) == [42]
    assert evaluate_fhirpath("{}.single()", {}) == []
    assert evaluate_fhirpath("iif(1 < 2, 'yes', 'no')", {}) == ["yes"]
    assert evaluate_fhirpath("iif(1 > 2, 'yes')", {}) == []


def test_string_and_conversion_functions() -> None:
    assert evaluate_fhirpath("'abc-123'.matches('[a-z]+-[0-9]+')", {}) == [True]
    assert evaluate_fhirpath("'abc-123'.matches('[a-z]+')", {}) == [False]
    assert evaluate_fhirpath("'a-b-c'.replaceMatches('-', '_')", {}) == ["a_b_c"]
    assert evaluate_fhirpath("'hello'.startsWith('he')", {}) == [True]
    assert evaluate_fhirpath("'hello'.endsWith('lo')", {}) == [True]
    assert evaluate_fhirpath("'hello'.contains('ell')", {}) == [True]
    assert evaluate_fhirpath("'abcdef'.substring(2, 3)", {}) == ["cde"]
    assert evaluate_fhirpath("'abcdef'.substring(2)", {}) == ["cdef"]
    assert evaluate_fhirpath("'abcdef'.substring(99)", {}) == []
    assert evaluate_fhirpath("'Hello'.length()", {}) == [5]
    assert evaluate_fhirpath("'Hello'.upper()", {}) == ["HELLO"]
    assert evaluate_fhirpath("'Hello'.lower()", {}) == ["hello"]
    assert evaluate_fhirpath("'abc'.toChars()", {}) == ["a", "b", "c"]
    assert evaluate_fhirpath("'42'.toInteger()", {}) == [42]
    assert evaluate_fhirpath("'3.5'.toDecimal()", {}) == [3.5]
    assert evaluate_fhirpath("true.toString()", {}) == ["true"]
    assert evaluate_fhirpath("'42'.convertsToInteger()", {}) == [True]
    assert evaluate_fhirpath("'nope'.convertsToInteger()", {}) == [False]
    assert evaluate_fhirpath("'3.5'.convertsToDecimal()", {}) == [True]


def test_type_tree_collection_extension_and_resolve() -> None:
    obs = {
        "resourceType": "Observation",
        "id": "o1",
        "valueQuantity": {"value": 10, "unit": "mg"},
        "subject": {"reference": "#p1"},
        "performer": [{"reference": "Practitioner/pr1"}],
        "contained": [{"resourceType": "Patient", "id": "p1", "name": [{"family": "Smith"}]}],
        "extension": [{"url": "http://example.org/ext", "valueString": "v1"}],
    }
    bundle_index = {"Practitioner/pr1": {"resourceType": "Practitioner", "id": "pr1"}}

    assert evaluate_fhirpath("is(FHIR.Observation)", obs) == [True]
    assert evaluate_fhirpath("obs is Patient", {"obs": obs}) == [False]
    assert evaluate_fhirpath("value.is(Quantity)", obs) == [True]
    assert evaluate_fhirpath("(value | id).ofType(Quantity).value", obs) == [10]
    assert evaluate_fhirpath("(value as Quantity).unit", obs) == ["mg"]
    assert evaluate_fhirpath("extension('http://example.org/ext').value", obs) == ["v1"]
    assert evaluate_fhirpath("subject.resolve().name.family", obs) == ["Smith"]
    assert evaluate_fhirpath("performer.resolve().id", obs, bundle_index=bundle_index) == ["pr1"]
    assert evaluate_fhirpath("descendants().where($this is Patient).id", obs) == ["p1"]
    assert evaluate_fhirpath("(1 | 2 | 3).intersect(2 | 3 | 4)", {}) == [2, 3]
    assert evaluate_fhirpath("(1 | 2).union(2 | 3)", {}) == [1, 2, 3]
    assert evaluate_fhirpath("(1 | 2 | 3).exclude(2)", {}) == [1, 3]
    assert evaluate_fhirpath("(1 | 2).subsetOf(1 | 2 | 3)", {}) == [True]
    assert evaluate_fhirpath("(1 | 2 | 3).supersetOf(1 | 2)", {}) == [True]
    assert evaluate_fhirpath("id.trace('debug')", obs) == ["o1"]


# ---------------------------------------------------------------------------
# Real R4 / US-Core / IPS Invariants
# ---------------------------------------------------------------------------


def test_real_r4_invariants() -> None:
    # ele-1
    ele_1 = "hasValue() or (children().count() > id.count())"
    assert evaluate_fhirpath_invariant(ele_1, {"id": "1"}) is False
    assert evaluate_fhirpath_invariant(ele_1, {"id": "1", "value": "x"}) is True

    # ext-1
    ext_1 = "extension.exists() != value.exists()"
    assert evaluate_fhirpath_invariant(ext_1, {"url": "u", "valueString": "v"}) is True
    assert (
        evaluate_fhirpath_invariant(
            ext_1, {"url": "u", "valueString": "v", "extension": [{"url": "sub"}]}
        )
        is False
    )

    # dom-2, dom-6
    dom_2 = "contained.contained.empty()"
    assert evaluate_fhirpath_invariant(dom_2, {"contained": [{"id": "1"}]}) is True
    assert (
        evaluate_fhirpath_invariant(dom_2, {"contained": [{"id": "1", "contained": [{"id": "2"}]}]})
        is False
    )
    dom_6 = "text.`div`.exists()"
    assert evaluate_fhirpath_invariant(dom_6, {"text": {"div": "<div/>"}}) is True
    assert evaluate_fhirpath_invariant(dom_6, {"text": {"status": "generated"}}) is False

    # dom-3
    dom_3 = (
        "contained.where((('#'+id in (%resource.descendants().reference | "
        "%resource.descendants().as(canonical) | %resource.descendants().as(uri))) or "
        "descendants().where(reference = '#').exists() or "
        "descendants().where(as(canonical) = '#').exists() or "
        "descendants().where(as(uri) = '#').exists()).not()).trace('unmatched', id).empty()"
    )
    res_ok = {
        "resourceType": "Observation",
        "subject": {"reference": "#p1"},
        "contained": [{"resourceType": "Patient", "id": "p1"}],
    }
    res_orphan = {
        "resourceType": "Observation",
        "contained": [{"resourceType": "Patient", "id": "p1"}],
    }
    assert evaluate_fhirpath_invariant(dom_3, res_ok) is True
    assert evaluate_fhirpath_invariant(dom_3, res_orphan) is False


def test_real_ref_obs_con_and_us_core_invariants() -> None:
    res_ok = {
        "resourceType": "Observation",
        "subject": {"reference": "#p1"},
        "contained": [{"resourceType": "Patient", "id": "p1"}],
    }
    # ref-1
    ref_1 = (
        "reference.exists() implies (reference.startsWith('#').not() or "
        "(reference.substring(1).trace('url') in %rootResource.contained.id))"
    )
    ctx = EvalContext(resource=res_ok, root_resource=res_ok, context_item=res_ok["subject"])
    assert evaluate_fhirpath_invariant(ref_1, res_ok["subject"], ctx=ctx) is True
    assert evaluate_fhirpath_invariant(ref_1, {"reference": "#missing"}, ctx=ctx) is False

    # obs-7
    obs_7 = (
        "value.empty() or "
        "component.code.where(coding.intersect(%resource.code.coding).exists()).empty()"
    )
    obs_bad = {
        "resourceType": "Observation",
        "code": {"coding": [{"system": "http://loinc.org", "code": "123"}]},
        "valueQuantity": {"value": 1},
        "component": [{"code": {"coding": [{"system": "http://loinc.org", "code": "123"}]}}],
    }
    assert evaluate_fhirpath_invariant(obs_7, obs_bad) is False

    # con-5
    con_5 = "patient.exists() implies (patient.reference.exists() or patient.display.exists())"
    assert evaluate_fhirpath_invariant(con_5, {"patient": {"reference": "Patient/1"}}) is True
    assert evaluate_fhirpath_invariant(con_5, {"patient": {"type": "Patient"}}) is False

    # us-core-16 & us-core-17 (Luhn check digit on 10-digit NPI) & us-core-23..25
    us_core_16 = "telecom.where(system='phone').exists()"
    assert evaluate_fhirpath_invariant(us_core_16, {"telecom": [{"system": "phone"}]}) is True
    assert evaluate_fhirpath_invariant(us_core_16, {"telecom": [{"system": "email"}]}) is False

    luhn_expr = (
        "value.matches('^[0-9]{10}$') implies "
        "((value.substring(9, 1).toInteger() = "
        "((10 - ((value.substring(0, 1).toInteger() * 2).toString().toChars()"
        ".select($this.toInteger()).first() + 0) mod 10) mod 10)) "
        "or value.startsWith('1234567893'))"
    )
    assert evaluate_fhirpath_invariant(luhn_expr, {"value": "1234567893"}) is True

    us_core_23 = "category.exists() and code.exists()"
    us_core_24 = "effective.exists() or dataAbsentReason.exists()"
    us_core_25 = "performer.exists() implies performer.all(reference.exists() or display.exists())"
    assert evaluate_fhirpath_invariant(us_core_23, {"category": [{}], "code": {}}) is True
    assert evaluate_fhirpath_invariant(us_core_24, {"effectiveDateTime": "2024-01-01"}) is True
    assert evaluate_fhirpath_invariant(us_core_25, {"performer": [{"display": "Dr. A"}]}) is True
    assert evaluate_fhirpath_invariant(us_core_25, {"performer": [{}]}) is False


# ---------------------------------------------------------------------------
# Error Handling & Fail-Open Invariant Mode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad_expr",
    [
        "",
        "   ",
        "'unterminated",
        "`unterminated",
        "/* unterminated",
        "@",
        "$",
        "%",
        "1 +",
        "unknownFunc()",
        "$unknownVar",
        "%unknownEnv",
        "exists(1, 2)",
        "empty(1)",
        "where()",
        "matches('a', 'b')",
        "'abc'.matches('[unclosed')",
        "1 ? 2",
    ],
)
def test_compile_and_eval_errors(bad_expr: str) -> None:
    with pytest.raises(ValueError, match=r".+"):
        evaluate_fhirpath(bad_expr, {})


def test_invariant_fail_open_vs_strict() -> None:
    assert evaluate_fhirpath_invariant("unsupportedFunc()", {}) is True
    with pytest.raises(ValueError, match="Unsupported FHIRPath function"):
        evaluate_fhirpath_invariant("unsupportedFunc()", {}, strict=True)
    assert evaluate_fhirpath_invariant("{}", {}) is True
    assert evaluate_fhirpath_invariant("false", {}) is False
    assert compile_fhirpath("id") is compile_fhirpath("id")


def test_type_conversions_and_subsetting_edge_cases() -> None:
    assert evaluate_fhirpath("toInteger()", True) == [1]
    assert evaluate_fhirpath("toInteger()", False) == [0]
    assert evaluate_fhirpath("toInteger()", 7) == [7]
    assert evaluate_fhirpath("toInteger()", {}) == []
    assert evaluate_fhirpath("toDecimal()", True) == [1.0]
    assert evaluate_fhirpath("toDecimal()", False) == [0.0]
    assert evaluate_fhirpath("toDecimal()", 7) == [7.0]
    assert evaluate_fhirpath("toDecimal()", {}) == []
    assert evaluate_fhirpath("toString()", 7) == ["7"]
    assert evaluate_fhirpath("toString()", {}) == []
    assert evaluate_fhirpath("convertsToInteger()", None) == []
    assert evaluate_fhirpath("convertsToDecimal()", None) == []
    assert evaluate_fhirpath("hasValue()", [1, 2]) == [False]
    assert evaluate_fhirpath("tail()", [1]) == []
    assert evaluate_fhirpath("skip(-1)", [1, 2]) == [1, 2]
    assert evaluate_fhirpath("skip('bad')", [1, 2]) == []
    assert evaluate_fhirpath("take(0)", [1, 2]) == []
    assert evaluate_fhirpath("substring(0, -1)", "abc") == []


def test_tree_equiv_and_lexer_edge_cases() -> None:
    assert evaluate_fhirpath("children()", [1, {"a": [2], "b": None}]) == [2]
    assert evaluate_fhirpath("extension(123)", {"extension": []}) == []
    assert evaluate_fhirpath("extension('u')", ["not_dict"]) == []
    assert evaluate_fhirpath("resolve()", [{"reference": "#missing"}, 123]) == []
    assert evaluate_fhirpath("resolve()", {"reference": "Patient/1"}) == []
    assert evaluate_fhirpath("items ~ other", {"items": [1], "other": [1, 2]}) == [False]
    assert evaluate_fhirpath("items ~ other", {"items": {"a": 1}, "other": {"b": 1}}) == [False]
    assert evaluate_fhirpath("items ~ other", {"items": {"a": [1]}, "other": {"a": [1]}}) == [True]
    assert evaluate_fhirpath("items = other", {"items": [1], "other": [1, 2]}) == [False]
    assert evaluate_fhirpath("items is Observation", {"items": 1}) == [False]
    assert evaluate_fhirpath("items is Observation", {"items": True}) == [False]
    assert evaluate_fhirpath("items is decimal", {"items": 1.5}) == [True]
    assert evaluate_fhirpath("items is Quantity", {"items": {"unknown": 1}}) == [False]
    assert evaluate_fhirpath("`%`", {"%": 9}) == [9]
    assert evaluate_fhirpath("%`ucum`", {}) == ["http://unitsofmeasure.org"]
    assert evaluate_fhirpath("1.toString()", {}) == ["1"]
    assert evaluate_fhirpath("true // eof comment", {}) == [True]
    assert evaluate_fhirpath("1.5 + 2.5", {}) == [4.0]
    assert evaluate_fhirpath("true xor {}", {}) == []
    assert evaluate_fhirpath("1 < {}", {}) == []
    assert evaluate_fhirpath("'a'.matches(1)", {}) == []
    assert evaluate_fhirpath("'a'.replaceMatches(1, 'b')", {}) == []
    assert evaluate_fhirpath("(1 | 2).substring(0)", {}) == []
    assert evaluate_fhirpath("(1 | 2).length()", {}) == []
    assert evaluate_fhirpath("(1 | 2).upper()", {}) == []
    assert evaluate_fhirpath("(1 | 2).lower()", {}) == []
    assert evaluate_fhirpath("(1 | 2).toChars()", {}) == []
    assert evaluate_fhirpath("(1 | 2).toInteger()", {}) == []
    assert evaluate_fhirpath("(1 | 2).toDecimal()", {}) == []
    assert evaluate_fhirpath("(1 | 2).toString()", {}) == []
    assert evaluate_fhirpath("items.repeat(next)", {"items": {"id": 1}}) == []


@pytest.mark.parametrize(
    "bad_expr",
    [
        "a.\\",
        "'abc\\'",
        "a.",
        "1 2",
        "is(1)",
        "is(FHIR.1)",
        "exists(1, 2)",
        "not(1)",
        "hasValue(1)",
        "count(1)",
        "distinct(1)",
        "isDistinct(1)",
        "allTrue(1)",
        "anyTrue(1)",
        "allFalse(1)",
        "anyFalse(1)",
        "select()",
        "all()",
        "repeat()",
        "first(1)",
        "last(1)",
        "tail(1)",
        "skip()",
        "take()",
        "single(1)",
        "iif(true)",
        "matches()",
        "replaceMatches('a')",
        "startsWith()",
        "endsWith()",
        "contains()",
        "substring()",
        "length(1)",
        "upper(1)",
        "lower(1)",
        "toChars(1)",
        "toInteger(1)",
        "toDecimal(1)",
        "toString(1)",
        "convertsToInteger(1)",
        "convertsToDecimal(1)",
        "is()",
        "as()",
        "ofType()",
        "children(1)",
        "descendants(1)",
        "intersect()",
        "union()",
        "exclude()",
        "subsetOf()",
        "supersetOf()",
        "trace()",
        "extension()",
        "resolve(1)",
        "(1 | 2).single()",
        "(1 | 2).is(integer)",
        "(1 | 2) is integer",
        "(1 | 2) in (1 | 2)",
        "(1 | 2) contains (1 | 2)",
        "(1 | 2) and true",
        "'a'.replaceMatches('[bad', 'b')",
        f"'a'.matches('{'a' * 600}')",
        f"'a'.replaceMatches('{'a' * 600}', 'b')",
    ],
)
def test_more_error_branches(bad_expr: str) -> None:
    with pytest.raises(ValueError, match=r".+"):
        evaluate_fhirpath(bad_expr, {})
