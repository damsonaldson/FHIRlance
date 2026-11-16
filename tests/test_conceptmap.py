"""Tests for ConceptMap parsing, registry, IG loading, and $translate."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import patch

import fhirlance
import fhirlance.conceptmap as cm_mod
from fhirlance.conceptmap import (
    _TRANSLATE_L1_CACHE,
    ConceptMapRegistry,
    ConceptMapSpec,
    TranslateMatch,
    TranslateRequest,
    TranslateResult,
    parse_concept_map,
    translate_code,
)
from fhirlance.ig_loader import clear_ig_cache, load_ig_concept_maps
from fhirlance.terminology import TxClient, TxOptions


def _sample_concept_map() -> dict[str, Any]:
    return {
        "resourceType": "ConceptMap",
        "url": "http://example.org/fhir/ConceptMap/test-map",
        "version": "1.0.0",
        "name": "TestMap",
        "status": "active",
        "sourceUri": "http://example.org/fhir/ValueSet/src",
        "targetUri": "http://example.org/fhir/ValueSet/tgt",
        "group": [
            {
                "source": "http://example.org/cs/src",
                "sourceVersion": "2024",
                "target": "http://example.org/cs/tgt",
                "targetVersion": "2024",
                "element": [
                    {
                        "code": "A",
                        "display": "Alpha",
                        "target": [
                            {
                                "code": "X",
                                "display": "X-ray",
                                "equivalence": "equivalent",
                                "comment": "Exact match",
                            }
                        ],
                    },
                    {
                        "code": "B",
                        "target": [
                            {
                                "code": "Y1",
                                "equivalence": "narrower",
                                "dependsOn": [
                                    {
                                        "property": "http://example.org/prop/gender",
                                        "value": "female",
                                    }
                                ],
                            },
                            {
                                "code": "Y2",
                                "equivalence": "narrower",
                                "dependsOn": [
                                    {
                                        "property": "http://example.org/prop/gender",
                                        "value": "male",
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "code": "C",
                        "target": [
                            {
                                "equivalence": "unmatched",
                                "comment": "No equivalent code",
                            }
                        ],
                    },
                    {
                        "code": "D",
                        "target": [
                            {
                                "code": "Z",
                                "equivalence": "disjoint",
                            }
                        ],
                    },
                ],
                "unmapped": {
                    "mode": "fixed",
                    "code": "UNK",
                    "display": "Unknown",
                },
            }
        ],
    }


def test_exports_available_from_top_level() -> None:
    assert fhirlance.ConceptMapRegistry is ConceptMapRegistry
    assert fhirlance.ConceptMapSpec is ConceptMapSpec
    assert fhirlance.TranslateMatch is TranslateMatch
    assert fhirlance.TranslateRequest is TranslateRequest
    assert fhirlance.TranslateResult is TranslateResult
    assert fhirlance.parse_concept_map is parse_concept_map
    assert fhirlance.translate_code is translate_code
    assert fhirlance.load_ig_concept_maps is load_ig_concept_maps


def test_parse_concept_map_valid_and_invalid() -> None:
    assert parse_concept_map({"resourceType": "Patient"}) is None

    spec = parse_concept_map(_sample_concept_map())
    assert spec is not None
    assert spec.url == "http://example.org/fhir/ConceptMap/test-map"
    assert spec.version == "1.0.0"
    assert spec.source_uri == "http://example.org/fhir/ValueSet/src"
    assert spec.target_uri == "http://example.org/fhir/ValueSet/tgt"
    assert len(spec.groups) == 1
    assert len(spec.groups[0].elements) == 4
    assert spec.groups[0].unmapped is not None
    assert spec.groups[0].unmapped.mode == "fixed"


def test_parse_concept_map_skips_malformed_subentries() -> None:
    raw: dict[str, Any] = {
        "resourceType": "ConceptMap",
        "url": "http://example.org/cm/malformed",
        "group": [
            "not-a-dict",
            {
                "element": [
                    "not-a-dict",
                    {"display": "no-code"},
                    {
                        "code": "K1",
                        "target": [
                            "not-a-dict",
                            {"code": "T1"},  # missing equivalence
                            {
                                "code": "T2",
                                "equivalence": "equal",
                                "dependsOn": ["bad", {"property": "p"}],  # missing value
                            },
                        ],
                    },
                ],
                "unmapped": {"display": "missing-mode"},
            },
        ],
    }
    spec = parse_concept_map(raw)
    assert spec is not None
    assert len(spec.groups) == 1
    assert len(spec.groups[0].elements) == 1
    assert len(spec.groups[0].elements[0].targets) == 1
    assert spec.groups[0].elements[0].targets[0].code == "T2"
    assert spec.groups[0].unmapped is None


def test_registry_indexing_and_lookup() -> None:
    reg = ConceptMapRegistry()
    assert reg.register_dict({"resourceType": "ValueSet"}) is None

    spec = reg.register_dict(_sample_concept_map())
    assert spec is not None

    by_url = reg.find_maps(url="http://example.org/fhir/ConceptMap/test-map")
    assert len(by_url) == 1

    by_ver = reg.find_maps(url="http://example.org/fhir/ConceptMap/test-map|1.0.0")
    assert len(by_ver) == 1

    by_pair = reg.find_maps(
        source="http://example.org/fhir/ValueSet/src",
        target="http://example.org/fhir/ValueSet/tgt",
    )
    assert len(by_pair) == 1

    by_group_pair = reg.find_maps(
        source="http://example.org/cs/src",
        target="http://example.org/cs/tgt",
    )
    assert len(by_group_pair) == 1

    assert reg.find_maps(source="http://example.org/other") == []
    cloned = reg.copy()
    assert len(cloned.find_maps(url=spec.url)) == 1


def test_translate_local_matches_and_equivalences() -> None:
    reg = ConceptMapRegistry()
    reg.register_dict(_sample_concept_map())

    res = translate_code(
        TranslateRequest(
            code="A",
            system="http://example.org/cs/src",
            url="http://example.org/fhir/ConceptMap/test-map",
        ),
        registry=reg,
    )
    assert res.result is True
    assert len(res.matches) == 1
    assert res.matches[0].code == "X"
    assert res.matches[0].system == "http://example.org/cs/tgt"
    assert res.matches[0].equivalence == "equivalent"

    unmatched = translate_code(TranslateRequest(code="C"), registry=reg)
    assert unmatched.result is False
    assert unmatched.message == "No equivalent code"
    assert unmatched.matches == ()

    disjoint = translate_code(TranslateRequest(code="D"), registry=reg)
    assert disjoint.result is False
    assert disjoint.matches == ()


def test_translate_local_depends_on() -> None:
    reg = ConceptMapRegistry()
    reg.register_dict(_sample_concept_map())

    res_f = translate_code(
        TranslateRequest(
            code="B",
            depends_on={"http://example.org/prop/gender": "female"},
        ),
        registry=reg,
    )
    assert res_f.result is True
    assert [m.code for m in res_f.matches] == ["Y1"]

    res_none = translate_code(TranslateRequest(code="B"), registry=reg)
    assert res_none.result is False


def test_translate_local_unmapped_fixed_and_provided() -> None:
    reg = ConceptMapRegistry()
    reg.register_dict(_sample_concept_map())

    fixed_res = translate_code(
        TranslateRequest(
            code="MISSING",
            url="http://example.org/fhir/ConceptMap/test-map",
        ),
        registry=reg,
    )
    assert fixed_res.result is True
    assert fixed_res.matches[0].code == "UNK"
    assert fixed_res.matches[0].display == "Unknown"

    provided_cm = {
        "resourceType": "ConceptMap",
        "url": "http://example.org/cm/provided",
        "group": [
            {
                "source": "http://example.org/s1",
                "target": "http://example.org/t1",
                "element": [],
                "unmapped": {"mode": "provided"},
            }
        ],
    }
    reg.register_dict(provided_cm)
    prov_res = translate_code(
        TranslateRequest(
            code="COPYME",
            url="http://example.org/cm/provided",
        ),
        registry=reg,
    )
    assert prov_res.result is True
    assert prov_res.matches[0].code == "COPYME"
    assert prov_res.matches[0].system == "http://example.org/t1"
    assert prov_res.matches[0].equivalence == "equivalent"


def test_translate_local_group_filters() -> None:
    reg = ConceptMapRegistry()
    reg.register_dict(_sample_concept_map())

    wrong_sys = translate_code(
        TranslateRequest(code="A", system="http://wrong"),
        registry=reg,
    )
    assert wrong_sys.result is False

    wrong_ver = translate_code(
        TranslateRequest(code="A", version="1999"),
        registry=reg,
    )
    assert wrong_ver.result is False

    wrong_tgt = translate_code(
        TranslateRequest(code="A", target_system="http://wrong-tgt"),
        registry=reg,
    )
    assert wrong_tgt.result is False


def test_translate_remote_with_cache(tmp_path: Path) -> None:
    _TRANSLATE_L1_CACHE.clear()
    db_path = tmp_path / "tx_cache.sqlite"
    client = TxClient(
        TxOptions(
            mode="remote",
            server="https://tx.example.org/r4",
            cache_path=db_path,
        )
    )
    response_payload = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": True},
            {"name": "message", "valueString": "Translated"},
            {
                "name": "match",
                "part": [
                    {"name": "equivalence", "valueCode": "equivalent"},
                    {
                        "name": "concept",
                        "valueCoding": {
                            "system": "http://loinc.org",
                            "code": "1234-5",
                            "display": "Test LOINC",
                        },
                    },
                    {"name": "source", "valueUri": "http://example.org/cm/remote"},
                ],
            },
        ],
    }

    class _FakeResp(io.BytesIO):
        def __enter__(self) -> _FakeResp:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    with patch(
        "urllib.request.urlopen",
        return_value=_FakeResp(json.dumps(response_payload).encode("utf-8")),
    ) as mock_open:
        req = TranslateRequest(
            code="A1",
            system="http://snomed.info/sct",
            target_system="http://loinc.org",
        )
        res1 = translate_code(req, tx_client=client)
        assert res1.result is True
        assert res1.message == "Translated"
        assert len(res1.matches) == 1
        assert res1.matches[0].code == "1234-5"
        assert mock_open.call_count == 1

        # L1 cache hit
        res2 = translate_code(req, tx_client=client)
        assert res2 == res1
        assert mock_open.call_count == 1

        # Clear L1 -> L2 SQLite cache hit
        _TRANSLATE_L1_CACHE.clear()
        res3 = translate_code(req, tx_client=client)
        assert res3 == res1
        assert mock_open.call_count == 1


def test_translate_remote_disabled_and_errors(tmp_path: Path) -> None:
    _TRANSLATE_L1_CACHE.clear()
    local_client = TxClient(TxOptions(mode="local"))
    res_disabled = translate_code(TranslateRequest(code="X"), tx_client=local_client)
    assert res_disabled.result is False

    bad_scheme = TxClient(
        TxOptions(mode="remote", server="ftp://bad.example.org", cache_path=tmp_path / "c1.db")
    )
    res_bad = translate_code(TranslateRequest(code="X"), tx_client=bad_scheme)
    assert res_bad.result is False
    assert res_bad.message is not None
    assert "Invalid URL scheme" in res_bad.message

    http_err_client = TxClient(
        TxOptions(mode="remote", server="https://tx.example.org/r4", cache_path=tmp_path / "c2.db")
    )
    with patch(
        "urllib.request.urlopen",
        side_effect=urllib.error.HTTPError(
            "https://tx.example.org/r4/ConceptMap/$translate",
            500,
            "Server Error",
            {},  # type: ignore[arg-type]
            None,
        ),
    ):
        res_http = translate_code(TranslateRequest(code="ERR"), tx_client=http_err_client)
        assert res_http.result is False
        assert res_http.message == "Terminology server HTTP 500"


def test_load_ig_concept_maps_and_cache(tmp_path: Path) -> None:
    clear_ig_cache()
    ig_dir = tmp_path / "my_ig"
    ig_dir.mkdir()
    cm_data = _sample_concept_map()
    (ig_dir / "ConceptMap-test.json").write_text(json.dumps(cm_data), encoding="utf-8")

    bundle_cm = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": [
            {
                "resource": {
                    "resourceType": "ConceptMap",
                    "url": "http://example.org/cm/bundled",
                    "group": [],
                }
            }
        ],
    }
    (ig_dir / "Bundle-cms.json").write_text(json.dumps(bundle_cm), encoding="utf-8")

    reg1 = load_ig_concept_maps([ig_dir])
    assert len(reg1.find_maps(url="http://example.org/fhir/ConceptMap/test-map")) == 1
    assert len(reg1.find_maps(url="http://example.org/cm/bundled")) == 1

    # Cached call
    reg2 = load_ig_concept_maps([ig_dir])
    assert len(reg2.find_maps(url="http://example.org/fhir/ConceptMap/test-map")) == 1
    clear_ig_cache()


def test_translate_local_reverse() -> None:
    reg = ConceptMapRegistry()
    reg.register_dict(_sample_concept_map())
    reg.register_dict(
        {
            "resourceType": "ConceptMap",
            "url": "http://example.org/cm/directional",
            "group": [
                {
                    "source": "http://example.org/cs/s",
                    "target": "http://example.org/cs/t",
                    "targetVersion": "v2",
                    "element": [
                        {
                            "code": "S1",
                            "display": "Source 1",
                            "target": [
                                {"code": "T1", "equivalence": "wider"},
                                {"code": "T2", "equivalence": "subsumes"},
                                {"code": "T3", "equivalence": "specializes"},
                                {"code": "T4", "equivalence": "unmatched", "comment": "Rev note"},
                            ],
                        }
                    ],
                }
            ],
        }
    )

    rev_eq = translate_code(
        TranslateRequest(
            code="X",
            system="http://example.org/cs/tgt",
            target_system="http://example.org/cs/src",
            url="http://example.org/fhir/ConceptMap/test-map",
            reverse=True,
        ),
        registry=reg,
    )
    assert rev_eq.result is True
    assert len(rev_eq.matches) == 1
    assert rev_eq.matches[0].code == "A"
    assert rev_eq.matches[0].display == "Alpha"
    assert rev_eq.matches[0].system == "http://example.org/cs/src"
    assert rev_eq.matches[0].equivalence == "equivalent"

    rev_narrower = translate_code(
        TranslateRequest(
            code="Y1",
            url="http://example.org/fhir/ConceptMap/test-map",
            depends_on={"http://example.org/prop/gender": "female"},
            reverse=True,
        ),
        registry=reg,
    )
    assert rev_narrower.result is True
    assert rev_narrower.matches[0].code == "B"
    assert rev_narrower.matches[0].equivalence == "wider"

    for tgt_code, expected_eq in (
        ("T1", "narrower"),
        ("T2", "specializes"),
        ("T3", "subsumes"),
    ):
        res = translate_code(
            TranslateRequest(
                code=tgt_code,
                url="http://example.org/cm/directional",
                version="v2",
                reverse=True,
            ),
            registry=reg,
        )
        assert res.result is True
        assert res.matches[0].code == "S1"
        assert res.matches[0].equivalence == expected_eq

    rev_note = translate_code(
        TranslateRequest(code="T4", url="http://example.org/cm/directional", reverse=True),
        registry=reg,
    )
    assert rev_note.result is False
    assert rev_note.message == "Rev note"

    # Reverse should not fall back to unmapped fixed/provided
    rev_missing = translate_code(
        TranslateRequest(
            code="NOT_THERE",
            url="http://example.org/fhir/ConceptMap/test-map",
            reverse=True,
        ),
        registry=reg,
    )
    assert rev_missing.result is False


def test_registry_multi_group_does_not_cross_match() -> None:
    reg = ConceptMapRegistry()
    spec = reg.register_dict(
        {
            "resourceType": "ConceptMap",
            "url": "http://example.org/cm/multi",
            "group": [
                {"source": "http://example.org/A", "target": "http://example.org/B", "element": []},
                {"source": "http://example.org/C", "target": "http://example.org/D", "element": []},
            ],
        }
    )
    assert spec is not None
    assert reg.find_maps(source="http://example.org/A", target="http://example.org/D") == []
    assert len(reg.find_maps(source="http://example.org/A", target="http://example.org/B")) == 1
    assert len(reg.find_maps(source="http://example.org/C", target="http://example.org/D")) == 1
    assert len(reg.find_maps(source="http://example.org/A")) == 1
    assert len(reg.find_maps(target="http://example.org/D")) == 1


def test_translate_remote_transient_errors_not_cached(tmp_path: Path) -> None:
    _TRANSLATE_L1_CACHE.clear()
    db_path = tmp_path / "transient.sqlite"
    client = TxClient(
        TxOptions(
            mode="remote",
            server="https://tx.example.org/r4",
            cache_path=db_path,
        )
    )
    ok_payload = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": True},
            {
                "name": "match",
                "part": [
                    {"name": "equivalence", "valueCode": "equivalent"},
                    {"name": "concept", "valueCoding": {"system": "http://s", "code": "OK"}},
                ],
            },
        ],
    }

    class _FakeResp(io.BytesIO):
        def __enter__(self) -> _FakeResp:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    req = TranslateRequest(code="TRANSIENT")
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            urllib.error.HTTPError(
                "https://tx.example.org/r4/ConceptMap/$translate",
                503,
                "Service Unavailable",
                {},  # type: ignore[arg-type]
                None,
            ),
            _FakeResp(json.dumps(ok_payload).encode("utf-8")),
        ],
    ) as mock_open:
        err_res = translate_code(req, tx_client=client)
        assert err_res.result is False
        assert err_res.message == "Terminology server HTTP 503"
        assert mock_open.call_count == 1

        # Must NOT have been cached in L1 or SQLite; second call hits server again
        ok_res = translate_code(req, tx_client=client)
        assert ok_res.result is True
        assert ok_res.matches[0].code == "OK"
        assert mock_open.call_count == 2

    # URLError and non-dict JSON are also not cached
    req2 = TranslateRequest(code="NETERR")
    with patch(
        "urllib.request.urlopen",
        side_effect=[
            urllib.error.URLError("timeout"),
            _FakeResp(b"[]"),
        ],
    ) as mock_open2:
        r_url = translate_code(req2, tx_client=client)
        assert r_url.result is False
        r_list = translate_code(req2, tx_client=client)
        assert r_list.result is False
        assert r_list.message == "Unexpected non-dict response"
        assert mock_open2.call_count == 2


def test_translate_remote_depends_on_and_l1_eviction(tmp_path: Path, monkeypatch: Any) -> None:
    _TRANSLATE_L1_CACHE.clear()
    monkeypatch.setattr(cm_mod, "_TRANSLATE_L1_CACHE_MAX", 2)
    db_path = tmp_path / "deps_evict.sqlite"
    client = TxClient(
        TxOptions(
            mode="remote",
            server="https://tx.example.org/r4",
            cache_path=db_path,
        )
    )
    captured_bodies: list[dict[str, Any]] = []

    class _FakeResp(io.BytesIO):
        def __enter__(self) -> _FakeResp:
            return self

        def __exit__(self, *args: object) -> None:
            self.close()

    def _fake_urlopen(req: urllib.request.Request, **_kwargs: Any) -> _FakeResp:
        assert isinstance(req.data, bytes)
        captured_bodies.append(json.loads(req.data.decode("utf-8")))
        return _FakeResp(
            json.dumps(
                {
                    "resourceType": "Parameters",
                    "parameter": [{"name": "result", "valueBoolean": True}],
                }
            ).encode("utf-8")
        )

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen):
        r1 = TranslateRequest(
            code="C1",
            version="1.0",
            reverse=True,
            depends_on={"http://prop": "v1"},
        )
        r2 = TranslateRequest(code="C1", depends_on={"http://prop": "v2"})
        r3 = TranslateRequest(code="C2")
        translate_code(r1, tx_client=client)
        translate_code(r2, tx_client=client)
        translate_code(r3, tx_client=client)

    assert len(captured_bodies) == 3
    dep_params = [p for p in captured_bodies[0]["parameter"] if p["name"] == "dependency"]
    assert len(dep_params) == 1
    assert dep_params[0]["part"][0] == {"name": "element", "valueUri": "http://prop"}
    assert len(_TRANSLATE_L1_CACHE) == 2


def test_conceptmap_edge_cases_and_coverage(tmp_path: Path) -> None:
    assert translate_code(TranslateRequest(code="X")).result is False

    empty_reg = ConceptMapRegistry()
    assert translate_code(TranslateRequest(code="X"), registry=empty_reg).result is False

    cm_other = {
        "resourceType": "ConceptMap",
        "url": "http://example.org/cm/other",
        "group": [
            {
                "element": "not-a-list",
                "unmapped": {"mode": "other"},
            }
        ],
    }
    empty_reg.register_dict(cm_other)
    assert (
        translate_code(
            TranslateRequest(code="X", url="http://example.org/cm/other"),
            registry=empty_reg,
        ).result
        is False
    )

    parsed_params = cm_mod._parse_translate_parameters(
        {
            "resourceType": "Parameters",
            "parameter": [
                "bad-param",
                {
                    "name": "match",
                    "part": [
                        "bad-part",
                        {"name": "equivalence", "valueCode": "unmatched"},
                        {"name": "comment", "valueString": "ignored"},
                    ],
                },
                {
                    "name": "match",
                    "part": [
                        {"name": "equivalence", "valueCode": "equivalent"},
                        {"name": "comment", "valueString": "kept"},
                    ],
                },
            ],
        }
    )
    assert len(parsed_params.matches) == 1
    assert parsed_params.matches[0].comment == "kept"

    assert cm_mod._deserialize_result("{bad-json") is None
    assert cm_mod._deserialize_result('{"result": "not-bool"}') is None

    # Directory path triggers sqlite3.Error / OSError gracefully
    dir_path = tmp_path / "is_a_dir"
    dir_path.mkdir()
    assert cm_mod._read_translate_sqlite(dir_path, "k") is None
    cm_mod._write_translate_sqlite(dir_path, "k", TranslateResult(result=True))
