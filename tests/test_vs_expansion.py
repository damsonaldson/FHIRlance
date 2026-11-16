"""Unit tests for fhirlance.vs_expansion."""

from __future__ import annotations

from fhirlance.vs_expansion import (
    build_code_system_hierarchy,
    eval_filter,
    eval_filters,
    expand_value_set_codes,
    merge_code_system_supplements,
)


def _sample_concepts() -> list[dict[str, object]]:
    return [
        {
            "code": "root",
            "inactive": False,
            "property": [{"code": "category", "valueCode": "top"}],
            "concept": [
                {
                    "code": "child-a",
                    "property": [
                        {"code": "status", "valueCode": "active"},
                        {"code": "codingProp", "valueCoding": {"system": "urn:x", "code": "X1"}},
                    ],
                    "concept": [
                        {
                            "code": "grandchild-a1",
                            "inactive": True,
                            "property": [{"code": "status", "valueCode": "retired"}],
                        }
                    ],
                },
                {
                    "code": "child-b",
                    "property": [{"code": "status", "valueCode": "deprecated"}],
                },
            ],
        }
    ]


def test_build_hierarchy_extracts_links_and_properties() -> None:
    concepts: list[object] = [
        "not-a-dict",
        {"display": "missing code"},
        *_sample_concepts(),
    ]
    h = build_code_system_hierarchy(concepts)
    assert h.codes == frozenset({"root", "child-a", "grandchild-a1", "child-b"})
    assert h.children["root"] == frozenset({"child-a", "child-b"})
    assert h.children["child-a"] == frozenset({"grandchild-a1"})
    assert h.descendants["root"] == frozenset({"child-a", "grandchild-a1", "child-b"})
    assert h.ancestors["grandchild-a1"] == frozenset({"root", "child-a"})
    assert h.property_values["root"]["inactive"] is False
    assert h.property_values["child-a"]["codingProp"] == "X1"
    assert h.property_values["grandchild-a1"]["inactive"] is True


def test_build_hierarchy_respects_depth_bound() -> None:
    node: dict[str, object] = {"code": "leaf"}
    for i in range(70):
        node = {"code": f"n{i}", "concept": [node]}
    h = build_code_system_hierarchy([node])
    assert "n69" in h.codes
    assert "leaf" not in h.codes


def test_eval_filter_hierarchy_operators() -> None:
    h = build_code_system_hierarchy(_sample_concepts())
    assert eval_filter(h, "concept", "is-a", "child-a") == frozenset({"child-a", "grandchild-a1"})
    assert eval_filter(h, "concept", "descendent-of", "root") == frozenset(
        {"child-a", "grandchild-a1", "child-b"}
    )
    assert eval_filter(h, "concept", "is-not-a", "child-a") == frozenset({"root", "child-b"})
    assert eval_filter(h, "concept", "child-of", "root") == frozenset({"child-a", "child-b"})
    assert eval_filter(h, "concept", "generalizes", "grandchild-a1") == frozenset(
        {"grandchild-a1", "child-a", "root"}
    )
    assert eval_filter(h, "concept", "generalizes", "missing") == frozenset()
    assert eval_filter(h, "concept", "unknown-op", "root") == frozenset()


def test_eval_filter_exists_eq_in_not_in_regex() -> None:
    h = build_code_system_hierarchy(_sample_concepts())
    assert eval_filter(h, "status", "exists", "true") == frozenset(
        {"child-a", "grandchild-a1", "child-b"}
    )
    assert eval_filter(h, "status", "exists", "false") == frozenset({"root"})
    assert eval_filter(h, "status", "exists", "maybe") == frozenset()

    assert eval_filter(h, "inactive", "=", "true") == frozenset({"grandchild-a1"})
    assert eval_filter(h, "concept", "=", "child-b") == frozenset({"child-b"})
    assert eval_filter(h, "concept", "=", "missing") == frozenset()

    assert eval_filter(h, "concept", "in", "root,child-b,missing") == frozenset({"root", "child-b"})
    assert eval_filter(h, "status", "in", "active,retired") == frozenset(
        {"child-a", "grandchild-a1"}
    )
    assert eval_filter(h, "concept", "not-in", "root,child-b") == frozenset(
        {"child-a", "grandchild-a1"}
    )
    assert eval_filter(h, "status", "not-in", "retired,deprecated") == frozenset(
        {"root", "child-a"}
    )

    assert eval_filter(h, "concept", "regex", r"child-[ab]") == frozenset({"child-a", "child-b"})
    assert eval_filter(h, "status", "regex", r"ret.*") == frozenset({"grandchild-a1"})
    assert eval_filter(h, "concept", "regex", "[invalid") == frozenset()
    assert eval_filter(h, "concept", "regex", "a" * 300) == frozenset()


def test_eval_filters_intersection() -> None:
    h = build_code_system_hierarchy(_sample_concepts())
    matched = eval_filters(
        [
            {"property": "concept", "op": "descendent-of", "value": "root"},
            {"property": "status", "op": "not-in", "value": "retired,deprecated"},
        ],
        h,
    )
    assert matched == frozenset({"child-a"})
    assert eval_filters([], h) == frozenset()


def test_merge_code_system_supplements_versioned_and_unversioned() -> None:
    code_systems: list[dict[str, object]] = [
        {
            "resourceType": "CodeSystem",
            "url": "http://example.org/cs/base",
            "version": "1.0.0",
            "content": "complete",
            "concept": [
                {"code": "A", "concept": [{"code": "A1"}]},
                {"code": "B"},
            ],
        },
        {
            "resourceType": "CodeSystem",
            "url": "http://example.org/cs/not-complete",
            "content": "fragment",
            "concept": [{"code": "X"}],
        },
        {
            "resourceType": "CodeSystem",
            "url": "http://example.org/cs/sup",
            "content": "supplement",
            "supplements": "http://example.org/cs/base|1.0.0",
            "concept": [
                {"code": "A1", "property": [{"code": "tag", "valueString": "extra"}]},
                {"code": "C"},
            ],
        },
        {
            "resourceType": "CodeSystem",
            "url": "http://example.org/cs/orphan-sup",
            "content": "supplement",
            "supplements": "http://example.org/cs/missing",
            "concept": [{"code": "Z"}],
        },
    ]
    merged = merge_code_system_supplements(code_systems)
    assert "http://example.org/cs/sup" not in merged
    assert "http://example.org/cs/not-complete" not in merged
    assert "http://example.org/cs/base" in merged
    assert "http://example.org/cs/base|1.0.0" in merged

    h = merged["http://example.org/cs/base|1.0.0"]
    assert h.codes == frozenset({"A", "A1", "B", "C"})
    assert h.property_values["A1"]["tag"] == "extra"
    assert merged["http://example.org/cs/base"] is h


def test_expand_value_set_codes_versioned_filters_and_exclude() -> None:
    code_systems: list[dict[str, object]] = [
        {
            "url": "http://example.org/cs/v",
            "version": "1.0.0",
            "content": "complete",
            "concept": [{"code": "old-1"}, {"code": "old-2"}],
        },
        {
            "url": "http://example.org/cs/v",
            "version": "2.0.0",
            "content": "complete",
            "concept": [
                {
                    "code": "new-1",
                    "concept": [{"code": "new-1a"}, {"code": "new-1b"}],
                },
                {"code": "new-2", "inactive": True},
            ],
        },
    ]
    hierarchies = merge_code_system_supplements(code_systems)
    resolved_vs = {
        "http://example.org/vs/imported|1.0": frozenset({"imp-1", "imp-2"}),
    }
    vs: dict[str, object] = {
        "compose": {
            "include": [
                {
                    "system": "http://example.org/cs/v",
                    "version": "1.0.0",
                },
                {
                    "system": "http://example.org/cs/v",
                    "version": "2.0.0",
                    "filter": [{"property": "concept", "op": "child-of", "value": "new-1"}],
                },
                {
                    "system": "http://example.org/cs/explicit",
                    "concept": [{"code": "exp-1"}],
                },
                {"valueSet": ["http://example.org/vs/imported|1.0"]},
            ],
            "exclude": [
                {
                    "system": "http://example.org/cs/v",
                    "version": "1.0.0",
                    "concept": [{"code": "old-2"}],
                },
                {
                    "system": "http://example.org/cs/v",
                    "version": "2.0.0",
                    "filter": [{"property": "concept", "op": "=", "value": "new-1b"}],
                },
                {"valueSet": ["http://example.org/vs/imported|1.0"]},
            ],
        }
    }
    codes, systems, complete = expand_value_set_codes(vs, hierarchies, resolved_vs)
    assert codes == frozenset({"old-1", "new-1a", "exp-1"})
    assert systems == frozenset({"http://example.org/cs/v", "http://example.org/cs/explicit"})
    assert complete is True


def test_expand_value_set_codes_external_and_expansion_contains() -> None:
    ext_vs: dict[str, object] = {
        "compose": {
            "include": [
                {"system": "http://snomed.info/sct"},
                {"valueSet": ["http://example.org/vs/unknown"]},
            ]
        }
    }
    codes, systems, complete = expand_value_set_codes(ext_vs, {})
    assert codes == frozenset()
    assert systems == frozenset({"http://snomed.info/sct"})
    assert complete is False

    exp_vs: dict[str, object] = {
        "expansion": {
            "contains": [
                {
                    "system": "http://example.org/sys|1.0",
                    "code": "P1",
                    "contains": [{"system": "http://example.org/sys", "code": "P2"}],
                }
            ]
        }
    }
    e_codes, e_sys, e_complete = expand_value_set_codes(exp_vs, {})
    assert e_codes == frozenset({"P1", "P2"})
    assert e_sys == frozenset({"http://example.org/sys"})
    assert e_complete is True


def test_edge_cases_for_properties_supplements_and_exclude() -> None:
    # Property entries with non-dict, missing code, and missing value*
    h = build_code_system_hierarchy(
        [
            {
                "code": "P",
                "property": [
                    "bad-entry",
                    {"valueCode": "no-code"},
                    {"code": "no-val"},
                    {"code": "ok", "valueCode": "yes"},
                ],
            }
        ]
    )
    assert h.property_values == {"P": {"ok": "yes"}}

    # Merge supplements: overlapping descendants + new properties + invalid/empty CS
    merged = merge_code_system_supplements(
        [
            {"url": "", "content": "complete", "concept": [{"code": "X"}]},
            {"url": "http://example.org/empty", "content": "complete", "concept": []},
            {
                "url": "http://example.org/base",
                "content": "complete",
                "concept": [{"code": "R", "concept": [{"code": "C1"}]}],
            },
            {
                "url": "http://example.org/sup1",
                "content": "supplement",
                "supplements": "http://example.org/base",
                "concept": [
                    {"code": "R", "concept": [{"code": "C2"}]},
                    {"code": "C1", "property": [{"code": "note", "valueString": "added"}]},
                ],
            },
            {"url": "http://example.org/bad-sup", "content": "supplement"},
        ]
    )
    assert "http://example.org/empty" not in merged
    assert merged["http://example.org/base"].children["R"] == frozenset({"C1", "C2"})
    assert merged["http://example.org/base"].property_values["C1"]["note"] == "added"

    # Expand with: filter on unknown system, unversioned exclude-all, exclude concept without sys,
    # and non-dict items in expansion.contains
    vs_unknown_filter: dict[str, object] = {
        "compose": {
            "include": [
                {
                    "system": "http://example.org/unknown",
                    "filter": [{"property": "concept", "op": "=", "value": "A"}],
                },
                {"system": "http://example.org/s1", "concept": [{"code": "K1"}, {"code": "K2"}]},
                {"system": "http://example.org/s2", "concept": [{"code": "M1"}]},
            ],
            "exclude": [
                {"system": "http://example.org/s2"},
                {"concept": [{"code": "K2"}]},
            ],
        }
    }
    codes, _, complete = expand_value_set_codes(vs_unknown_filter, {})
    assert codes == frozenset({"K1"})
    assert complete is False

    exp_bad: dict[str, object] = {"expansion": {"contains": ["bad", {"code": "OK"}]}}
    b_codes, b_sys, _ = expand_value_set_codes(exp_bad, {})
    assert b_codes == frozenset({"OK"})
    assert b_sys == frozenset()
