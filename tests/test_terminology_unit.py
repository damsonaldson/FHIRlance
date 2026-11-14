"""Unit tests for fhirlance terminology engine (offline grammars, caching, bindings)."""

from __future__ import annotations

import io
import json
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from fhirlance.terminology import (
    _L1_CACHE,
    DEFAULT_TX_SERVER,
    TxClient,
    TxOptions,
    _BindingContext,
    _build_remote_url,
    _check_grammar_system,
    _default_cache_db_path,
    _evaluate_code_in_valueset,
    _evaluate_external_code,
    _execute_remote_call,
    _init_sqlite_cache,
    _is_bracketed_with_exponent,
    _is_valid_ucum_leaf,
    _parse_parameters_response,
    _parse_ucum_tokens,
    _read_sqlite_cache,
    _record_binding_issue,
    _TxCacheKey,
    _validate_codeable_concept,
    _validate_one_binding_value,
    _write_sqlite_cache,
    is_valid_bcp47_code,
    is_valid_iso3166_code,
    is_valid_mime_code,
    is_valid_ucum_code,
    parse_tx_options,
    validate_binding_value,
    validate_remote_code,
    validate_standalone_codings,
)

# -----------------------------------------------------------------------------
# 1. Option Parsing
# -----------------------------------------------------------------------------


def test_parse_tx_options_instances() -> None:
    opt1 = TxOptions(mode="remote", server="https://tx.example.com", strict_extensible=False)
    opt2 = parse_tx_options(opt1, strict_extensible=True, cache_path=Path("/tmp/cache.sqlite"))
    assert opt2.mode == "remote"
    assert opt2.server == "https://tx.example.com"
    assert opt2.strict_extensible is True
    assert opt2.cache_path == Path("/tmp/cache.sqlite")

    # Keep existing if cache_path is None
    opt3 = parse_tx_options(opt2)
    assert opt3.cache_path == Path("/tmp/cache.sqlite")
    assert opt3.strict_extensible is True


def test_parse_tx_options_primitives() -> None:
    assert parse_tx_options(True).mode == "local"
    assert parse_tx_options(None).mode == "local"
    assert parse_tx_options(False).mode == "off"

    for off_val in ("off", "n/a", "na", "none", "false", "0"):
        assert parse_tx_options(off_val).mode == "off"

    for loc_val in ("local", "on", "true", "1"):
        assert parse_tx_options(loc_val).mode == "local"

    rem = parse_tx_options("remote")
    assert rem.mode == "remote"
    assert rem.server == DEFAULT_TX_SERVER

    custom = parse_tx_options("https://r4.ontoserver.csiro.au/fhir/")
    assert custom.mode == "remote"
    assert custom.server == "https://r4.ontoserver.csiro.au/fhir"

    with pytest.raises(ValueError, match="Unsupported terminology mode"):
        parse_tx_options("invalid-mode-string")

    with pytest.raises(ValueError, match="Unsupported terminology mode"):
        parse_tx_options(123)  # type: ignore[arg-type]


# -----------------------------------------------------------------------------
# 2. Grammar Validators: ISO-3166, MIME, BCP-47, UCUM
# -----------------------------------------------------------------------------


def test_iso3166_validation() -> None:
    assert not is_valid_iso3166_code("")
    assert not is_valid_iso3166_code(None)  # type: ignore[arg-type]
    assert not is_valid_iso3166_code(" CA ")  # whitespace
    assert not is_valid_iso3166_code("ZZ")  # non-existent alpha-2

    assert is_valid_iso3166_code("CA")
    assert is_valid_iso3166_code("US")
    assert is_valid_iso3166_code("GB")
    assert is_valid_iso3166_code("CAN")
    assert is_valid_iso3166_code("124")

    # Subdivisions (ISO-3166-2)
    assert is_valid_iso3166_code("CA-ON")
    assert is_valid_iso3166_code("US-CA")
    assert is_valid_iso3166_code("CA-ON", system="urn:iso:std:iso:3166:-2")
    assert not is_valid_iso3166_code("ZZ-ON")  # invalid country
    assert not is_valid_iso3166_code("CA-TOOLONG")  # invalid subtag format


def test_mime_validation() -> None:
    assert not is_valid_mime_code("")
    assert not is_valid_mime_code(None)  # type: ignore[arg-type]
    assert not is_valid_mime_code(" text/plain ")
    assert not is_valid_mime_code("not-a-mime")
    assert not is_valid_mime_code("invalid/sub/type")

    assert is_valid_mime_code("application/json")
    assert is_valid_mime_code("application/fhir+json")
    assert is_valid_mime_code("text/plain")
    assert is_valid_mime_code("image/png")
    assert is_valid_mime_code("video/mp4")
    assert is_valid_mime_code("chemical/x-cif")
    assert is_valid_mime_code("application/vnd.custom+xml; charset=utf-8")


def test_bcp47_validation() -> None:
    assert not is_valid_bcp47_code("")
    assert not is_valid_bcp47_code(None)  # type: ignore[arg-type]
    assert not is_valid_bcp47_code(" en ")
    assert not is_valid_bcp47_code("en_US")  # underscores not allowed
    assert not is_valid_bcp47_code("toolonglanguagecode")

    assert is_valid_bcp47_code("en")
    assert is_valid_bcp47_code("en-US")
    assert is_valid_bcp47_code("fr-CA")
    assert is_valid_bcp47_code("zh-Hant")
    assert is_valid_bcp47_code("es-419")
    assert is_valid_bcp47_code("de-CH-1901")


def test_ucum_validation_basic() -> None:
    assert not is_valid_ucum_code("")
    assert not is_valid_ucum_code(None)  # type: ignore[arg-type]
    assert not is_valid_ucum_code("mg / dL")  # whitespace invalid
    assert not is_valid_ucum_code("invalidUnitAtom")
    assert not is_valid_ucum_code("(mg/dL")  # unbalanced parens
    assert not is_valid_ucum_code("{score")  # unbalanced braces
    assert not is_valid_ucum_code("[in_i")  # unbalanced brackets
    assert not is_valid_ucum_code("[in{score}]")  # nested invalid delimiters
    assert not is_valid_ucum_code("mg{nested{brace}}")
    assert not is_valid_ucum_code("mg/")  # trailing operator
    assert not is_valid_ucum_code("mg.")  # trailing dot

    # Basic atoms
    assert is_valid_ucum_code("mg")
    assert is_valid_ucum_code("kg")
    assert is_valid_ucum_code("g")
    assert is_valid_ucum_code("cm")
    assert is_valid_ucum_code("mm")
    assert is_valid_ucum_code("s")
    assert is_valid_ucum_code("min")
    assert is_valid_ucum_code("h")
    assert is_valid_ucum_code("d")
    assert is_valid_ucum_code("a")
    assert is_valid_ucum_code("mol")
    assert is_valid_ucum_code("Cel")
    assert is_valid_ucum_code("1")
    assert is_valid_ucum_code("%")


def test_ucum_validation_compounds() -> None:
    # Exponents & division
    assert is_valid_ucum_code("cm2")
    assert is_valid_ucum_code("m3")
    assert is_valid_ucum_code("s-1")
    assert is_valid_ucum_code("m/s2")
    assert is_valid_ucum_code("mg/dL")
    assert is_valid_ucum_code("kg/m2")
    assert is_valid_ucum_code("/min")
    assert is_valid_ucum_code("10*3/uL")

    # Bracketed & Customary units
    assert is_valid_ucum_code("[in_i]")
    assert is_valid_ucum_code("[lb_av]")
    assert is_valid_ucum_code("[degF]")
    assert is_valid_ucum_code("[IU]")
    assert is_valid_ucum_code("[pH]")
    assert is_valid_ucum_code("mm[Hg]")
    assert is_valid_ucum_code("cm[H2O]")
    assert is_valid_ucum_code("[in_i]2")

    # Annotations & Nested expressions
    assert is_valid_ucum_code("{score}")
    assert is_valid_ucum_code("mg{total}/dL")
    assert is_valid_ucum_code("(mg/dL)")
    assert is_valid_ucum_code("(kg/(m.s))")
    assert is_valid_ucum_code("(mg/dL)2")


def test_ucum_corner_cases() -> None:
    # Bracketed exponent with unbracketed or invalid base
    assert not _is_bracketed_with_exponent("[unknown]2")
    # Empty leaf
    assert not _is_valid_ucum_leaf("")
    # Inner nested braces
    assert not _is_valid_ucum_leaf("mg{in{val}d}")
    # Empty token list in _parse_ucum_tokens
    assert not _parse_ucum_tokens([])


# -----------------------------------------------------------------------------
# 3. Two-Tier Cache & SQLite
# -----------------------------------------------------------------------------


def test_sqlite_cache_roundtrip(tmp_path: Path) -> None:
    db_file = tmp_path / "subdir" / "test_tx_cache.sqlite"
    conn = _init_sqlite_cache(db_file)
    assert conn is not None
    conn.close()

    key = _TxCacheKey(
        server="https://tx.example.com",
        system="http://loinc.org",
        code="883-9",
        value_set_url="http://hl7.org/fhir/ValueSet/observation-codes",
    )

    # Initial read returns None (miss)
    assert _read_sqlite_cache(db_file, key) is None

    # Write positive hit
    _write_sqlite_cache(db_file, key, True, "Valid LOINC code")
    read_val = _read_sqlite_cache(db_file, key)
    assert read_val == (True, "Valid LOINC code")

    # Overwrite negative hit
    _write_sqlite_cache(db_file, key, False, "Invalid code")
    read_val2 = _read_sqlite_cache(db_file, key)
    assert read_val2 == (False, "Invalid code")


def test_sqlite_cache_error_suppression(tmp_path: Path) -> None:
    # Target path that cannot be created (e.g. file is a directory or OS error)
    bad_path = tmp_path / "a_file"
    bad_path.write_text("not a dir", encoding="utf-8")
    uncreatable_db = bad_path / "cache.sqlite"

    assert _init_sqlite_cache(uncreatable_db) is None
    key = _TxCacheKey("srv", "sys", "code", "vs")
    assert _read_sqlite_cache(uncreatable_db, key) is None
    _write_sqlite_cache(uncreatable_db, key, True, None)


def test_default_cache_db_path() -> None:
    p = _default_cache_db_path()
    assert str(p).endswith("fhirlance-tx-cache.sqlite")


# -----------------------------------------------------------------------------
# 4. Remote Calls & Remote Code Validation
# -----------------------------------------------------------------------------


def test_build_remote_url() -> None:
    url_vs = _build_remote_url("https://tx.org", "http://loinc.org", "123", "http://vs.org")
    assert "ValueSet/$validate-code" in url_vs
    assert "url=http%3A%2F%2Fvs.org" in url_vs

    url_cs = _build_remote_url("https://tx.org", "http://loinc.org", "123", None)
    assert "CodeSystem/$validate-code" in url_cs
    assert "url=http%3A%2F%2Floinc.org" in url_cs


def test_parse_parameters_response() -> None:
    data: dict[str, Any] = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "result", "valueBoolean": True},
            {"name": "message", "valueString": "Concept is valid"},
            "ignored_non_dict",
        ],
    }
    res, msg = _parse_parameters_response(data)
    assert res is True
    assert msg == "Concept is valid"


def test_execute_remote_call_invalid_scheme() -> None:
    res, msg = _execute_remote_call("ftp://invalid-scheme.org", timeout=1.0)
    assert res is False
    assert "Invalid URL scheme" in (msg or "")


def test_execute_remote_call_success() -> None:
    response_json = json.dumps(
        {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "result", "valueBoolean": True},
                {"name": "message", "valueString": "Valid code"},
            ],
        }
    ).encode("utf-8")

    mock_resp = MagicMock()
    mock_resp.read.return_value = response_json
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res, msg = _execute_remote_call("https://tx.fhir.org/r4/ValueSet/$validate-code", 5.0)
        assert res is True
        assert msg == "Valid code"


def test_execute_remote_call_non_dict_json() -> None:
    mock_resp = MagicMock()
    mock_resp.read.return_value = b'["not", "a", "dict"]'
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res, msg = _execute_remote_call("https://tx.fhir.org/r4/ValueSet/$validate-code", 5.0)
        assert res is None
        assert "Unexpected non-dict response" in (msg or "")


def test_execute_remote_call_http_error_with_payload() -> None:
    err_body = json.dumps(
        {
            "resourceType": "Parameters",
            "parameter": [
                {"name": "result", "valueBoolean": False},
                {"name": "message", "valueString": "Code not found"},
            ],
        }
    ).encode("utf-8")
    http_err = urllib.error.HTTPError(
        url="https://tx.fhir.org",
        code=404,
        msg="Not Found",
        hdrs={},  # type: ignore[arg-type]
        fp=io.BytesIO(err_body),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        res, msg = _execute_remote_call("https://tx.fhir.org/r4/ValueSet/$validate-code", 5.0)
        assert res is False
        assert msg == "Code not found"


def test_execute_remote_call_http_error_without_payload() -> None:
    http_err = urllib.error.HTTPError(
        url="https://tx.fhir.org",
        code=500,
        msg="Internal Error",
        hdrs={},  # type: ignore[arg-type]
        fp=io.BytesIO(b"internal server error"),
    )

    with patch("urllib.request.urlopen", side_effect=http_err):
        res, msg = _execute_remote_call("https://tx.fhir.org/r4/ValueSet/$validate-code", 5.0)
        assert res is None
        assert "Terminology server HTTP 500" in (msg or "")


def test_execute_remote_call_network_error() -> None:
    url_err = urllib.error.URLError("Connection refused")
    with patch("urllib.request.urlopen", side_effect=url_err):
        res, msg = _execute_remote_call("https://tx.fhir.org/r4/ValueSet/$validate-code", 5.0)
        assert res is None
        assert "Terminology server unreachable" in (msg or "")


def test_validate_remote_code_modes_and_caching(tmp_path: Path) -> None:
    _L1_CACHE.clear()
    db_file = tmp_path / "cache.sqlite"

    # 1. Mode off -> None
    opt_off = TxOptions(mode="off")
    assert validate_remote_code(options=opt_off, system="sys", code="code") == (None, None)

    # 2. Mode local -> None
    opt_local = TxOptions(mode="local")
    assert validate_remote_code(options=opt_local, system="sys", code="code") == (None, None)

    # 3. Mode remote with L1 hit
    opt_remote = TxOptions(mode="remote", cache_path=db_file)
    _L1_CACHE[("https://tx.fhir.org/r4", "http://loinc.org", "883-9", "")] = (True, "L1 Cached")
    assert validate_remote_code(options=opt_remote, system="http://loinc.org", code="883-9") == (
        True,
        "L1 Cached",
    )

    # 4. Mode remote with L2 SQLite hit
    _L1_CACHE.clear()
    key = _TxCacheKey("https://tx.fhir.org/r4", "http://loinc.org", "999-9", "")
    _write_sqlite_cache(db_file, key, True, "L2 Cached")
    res, msg = validate_remote_code(options=opt_remote, system="http://loinc.org", code="999-9")
    assert res is True
    assert msg == "L2 Cached"
    # Verify it was elevated to L1
    assert _L1_CACHE[("https://tx.fhir.org/r4", "http://loinc.org", "999-9", "")] == (
        True,
        "L2 Cached",
    )

    # 5. Remote network call on cache miss
    _L1_CACHE.clear()
    response_json = json.dumps(
        {
            "resourceType": "Parameters",
            "parameter": [{"name": "result", "valueBoolean": True}],
        }
    ).encode("utf-8")
    mock_resp = MagicMock()
    mock_resp.read.return_value = response_json
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp):
        res2, _ = validate_remote_code(
            options=opt_remote, system="http://loinc.org", code="12345-6"
        )
        assert res2 is True
        # Verify cached in L1 and L2
        assert (
            "https://tx.fhir.org/r4",
            "http://loinc.org",
            "12345-6",
            "",
        ) in _L1_CACHE


def test_tx_client_class() -> None:
    client = TxClient(TxOptions(mode="local"))
    assert client.validate_code("http://sys", "code") == (None, None)

    client_default = TxClient()
    assert client_default.options.mode == "local"


def test_grammar_system_dispatch() -> None:
    assert _check_grammar_system("http://unitsofmeasure.org", "mg") == (True, True)
    assert _check_grammar_system("urn:ietf:bcp:47", "en-US") == (True, True)
    assert _check_grammar_system("urn:ietf:bcp:13", "application/json") == (True, True)
    assert _check_grammar_system("http://hl7.org/fhir/ValueSet/mimetypes", "image/png") == (
        True,
        True,
    )
    assert _check_grammar_system("urn:iso:std:iso:3166", "CA") == (True, True)
    assert _check_grammar_system("http://other.system", "code") == (False, True)


def test_evaluate_code_in_valueset_branches() -> None:
    # 1. Grammar system invalid code
    r1, m1 = _evaluate_code_in_valueset(
        "http://unitsofmeasure.org", "invalid ucum", "http://vs", None, TxOptions()
    )
    assert r1 is False
    assert "Invalid code" in (m1 or "")

    # 2. Grammar system with vs_spec codes
    spec_ucum = {"codes": ["mg", "kg"]}
    r2, _ = _evaluate_code_in_valueset(
        "http://unitsofmeasure.org", "mg", "http://vs", spec_ucum, TxOptions()
    )
    assert r2 is True

    r3, _ = _evaluate_code_in_valueset(
        "http://unitsofmeasure.org", "g", "http://vs", spec_ucum, TxOptions()
    )
    assert r3 is False

    # 3. Grammar system with vs_spec is None
    r4, _ = _evaluate_code_in_valueset(
        "http://unitsofmeasure.org", "mg", "http://vs", None, TxOptions()
    )
    assert r4 is True

    # 4. System in system_codes
    spec_sys = {"system_codes": {"http://loinc.org": ["883-9"]}}
    r5, _ = _evaluate_code_in_valueset(
        "http://loinc.org", "883-9", "http://vs", spec_sys, TxOptions()
    )
    assert r5 is True

    r6, _ = _evaluate_code_in_valueset(
        "http://loinc.org", "999-9", "http://vs", spec_sys, TxOptions()
    )
    assert r6 is False

    # 5. No system provided, matches across system_codes or codes
    r7, _ = _evaluate_code_in_valueset("", "883-9", "http://vs", spec_sys, TxOptions())
    assert r7 is True

    r8, _ = _evaluate_code_in_valueset("", "000-0", "http://vs", spec_sys, TxOptions())
    assert r8 is False


def test_evaluate_external_code() -> None:
    # vs_spec is None -> True
    assert _evaluate_external_code("sys", "code", "vs", None, TxOptions()) == (True, None)

    # system in external_systems and code in codes -> True
    spec = {"external_systems": ["http://snomed.info/sct"], "codes": ["12345"]}
    assert _evaluate_external_code("http://snomed.info/sct", "12345", "vs", spec, TxOptions()) == (
        True,
        None,
    )

    # system in external_systems and local mode -> True
    assert _evaluate_external_code(
        "http://snomed.info/sct", "99999", "vs", spec, TxOptions(mode="local")
    ) == (True, None)

    # system in external_systems and remote mode -> calls remote
    _L1_CACHE[("https://tx.fhir.org/r4", "http://snomed.info/sct", "99999", "vs")] = (
        True,
        "Valid SNOMED",
    )
    assert _evaluate_external_code(
        "http://snomed.info/sct", "99999", "vs", spec, TxOptions(mode="remote")
    ) == (True, "Valid SNOMED")

    # system not in external_systems -> False
    assert _evaluate_external_code("http://other.system", "1", "vs", spec, TxOptions()) == (
        False,
        None,
    )


# -----------------------------------------------------------------------------
# 5. Binding Value Validation
# -----------------------------------------------------------------------------


def test_record_binding_issue_branches() -> None:
    ctx = _BindingContext(
        path="status",
        vs_url="http://vs",
        strength="extensible",
        options=TxOptions(),
        vs_spec=None,
        profile_prefix="",
    )
    # res is None -> warning
    errs, warns = _record_binding_issue("http://sys", "code", None, "timeout", ctx)
    assert errs == []
    assert len(warns) == 1
    assert "could not validate code" in warns[0]

    # unknown strength -> empty
    ctx_other = _BindingContext(
        path="status",
        vs_url="http://vs",
        strength="preferred",
        options=TxOptions(),
        vs_spec=None,
        profile_prefix="",
    )
    errs2, warns2 = _record_binding_issue("http://sys", "code", False, None, ctx_other)
    assert errs2 == []
    assert warns2 == []


def test_validate_codeable_concept_warning_and_text() -> None:
    ctx = _BindingContext(
        path="code",
        vs_url="http://vs",
        strength="extensible",
        options=TxOptions(mode="remote"),
        vs_spec={"external_systems": ["http://loinc.org"]},
        profile_prefix="",
    )
    cc = {"coding": [{"system": "http://loinc.org", "code": "down-code"}]}
    with patch(
        "fhirlance.terminology.validate_remote_code",
        return_value=(None, "Server down"),
    ):
        errs, warns = _validate_codeable_concept(cc, ctx)
        assert errs == []
        assert len(warns) == 1
        assert "could not validate code" in warns[0]

    # Text only with extensible binding -> passes
    cc_text = {"text": "Blood pressure"}
    errs_t, warns_t = _validate_codeable_concept(cc_text, ctx)
    assert errs_t == []
    assert warns_t == []


def test_validate_one_binding_value_non_primitive() -> None:
    ctx = _BindingContext(
        path="val",
        vs_url="http://vs",
        strength="required",
        options=TxOptions(),
        vs_spec=None,
        profile_prefix="",
    )
    errs, warns = _validate_one_binding_value(12345, ctx)
    assert errs == []
    assert warns == []


def test_validate_binding_value_modes_and_primitives() -> None:
    # Mode off returns empty
    res_off = validate_binding_value("active", "status", "http://vs", "required", TxOptions("off"))
    assert res_off.errors == []
    assert res_off.warnings == []

    # None value returns empty
    res_none = validate_binding_value(None, "status", "http://vs", "required", TxOptions("local"))
    assert res_none.errors == []
    assert res_none.warnings == []

    # Simple string code with required strength
    spec = {"codes": ["active", "suspended"]}
    res_ok = validate_binding_value(
        "active", "status", "http://vs", "required", TxOptions("local"), vs_spec=spec
    )
    assert res_ok.errors == []

    res_err = validate_binding_value(
        "unknown", "status", "http://vs", "required", TxOptions("local"), vs_spec=spec
    )
    assert len(res_err.errors) == 1
    assert "not in required ValueSet" in res_err.errors[0]

    # vs_spec as list or set normalization
    res_list_spec = validate_binding_value(
        "active", "status", "http://vs", "required", TxOptions("local"), vs_spec=["active"]
    )
    assert res_list_spec.errors == []


def test_validate_binding_extensible_and_strict() -> None:
    spec = {
        "codes": ["active"],
        "system_codes": {"http://hl7.org/fhir/contact-point-system": ["phone", "email"]},
    }
    # Extensible with known system -> error
    coding_known = {"system": "http://hl7.org/fhir/contact-point-system", "code": "fax"}
    res_ext = validate_binding_value(
        coding_known, "telecom.system", "http://vs", "extensible", TxOptions("local"), vs_spec=spec
    )
    assert len(res_ext.errors) == 1

    # Extensible with unknown system and not strict -> warning
    coding_other = {"system": "http://custom-system.org", "code": "custom-val"}
    res_warn = validate_binding_value(
        coding_other, "telecom.system", "http://vs", "extensible", TxOptions("local"), vs_spec=spec
    )
    assert res_warn.errors == []
    assert len(res_warn.warnings) == 1
    assert "not in extensible ValueSet" in res_warn.warnings[0]

    # Extensible with unknown system and strict_extensible=True -> error
    res_strict = validate_binding_value(
        coding_other,
        "telecom.system",
        "http://vs",
        "extensible",
        TxOptions("local", strict_extensible=True),
        vs_spec=spec,
    )
    assert len(res_strict.errors) == 1


def test_validate_binding_codeable_concept_and_lists() -> None:
    spec = {
        "codes": ["883-9"],
        "system_codes": {"http://loinc.org": ["883-9"]},
    }
    # Empty concept dict
    assert validate_binding_value({}, "code", "http://vs", "required", TxOptions()).errors == []

    # CodeableConcept with at least one valid coding passes
    cc_valid = {
        "coding": [
            {"system": "http://loinc.org", "code": "883-9"},
            {"system": "http://loinc.org", "code": "999-9"},
        ]
    }
    res_cc = validate_binding_value(
        cc_valid, "code", "http://vs", "required", TxOptions("local"), vs_spec=spec
    )
    assert res_cc.errors == []

    # CodeableConcept with only invalid coding fails
    cc_invalid = {"coding": [{"system": "http://loinc.org", "code": "000-0"}]}
    res_inv = validate_binding_value(
        cc_invalid, "code", "http://vs", "required", TxOptions("local"), vs_spec=spec
    )
    assert len(res_inv.errors) == 1

    # Text only on required binding produces error
    cc_text = {"text": "Blood pressure"}
    res_text = validate_binding_value(
        cc_text, "code", "http://vs", "required", TxOptions("local"), vs_spec=spec
    )
    assert len(res_text.errors) == 1

    # List of items
    res_list = validate_binding_value(
        ["active", "unknown"],
        "status",
        "http://vs",
        "required",
        TxOptions("local"),
        vs_spec={"codes": ["active"]},
    )
    assert len(res_list.errors) == 1


# -----------------------------------------------------------------------------
# 6. Standalone Codings Validation
# -----------------------------------------------------------------------------


def test_validate_standalone_codings() -> None:
    # Mode off returns empty
    res_off = validate_standalone_codings({"resourceType": "Patient"}, TxOptions("off"))
    assert res_off.errors == []

    # Language field validation (BCP-47)
    res_lang_ok = validate_standalone_codings(
        {"resourceType": "Patient", "language": "en-US"}, TxOptions("local")
    )
    assert res_lang_ok.errors == []

    res_lang_err = validate_standalone_codings(
        {"resourceType": "Patient", "language": "invalid_lang_tag"}, TxOptions("local")
    )
    assert len(res_lang_err.errors) == 1
    assert "urn:ietf:bcp:47" in res_lang_err.errors[0]

    # Grammar systems: UCUM in Quantity or Coding
    res_ucum_ok = validate_standalone_codings(
        {
            "resourceType": "Observation",
            "valueQuantity": {
                "system": "http://unitsofmeasure.org",
                "code": "mg/dL",
            },
        },
        TxOptions("local"),
    )
    assert res_ucum_ok.errors == []

    res_ucum_err = validate_standalone_codings(
        {
            "resourceType": "Observation",
            "valueQuantity": {
                "system": "http://unitsofmeasure.org",
                "code": "invalid / ucum",
            },
        },
        TxOptions("local"),
    )
    assert len(res_ucum_err.errors) == 1
    assert "in grammar system" in res_ucum_err.errors[0]
    assert "unitsofmeasure.org" in res_ucum_err.errors[0]

    # Complete CodeSystems lookup
    complete_cs = {
        "http://hl7.org/fhir/administrative-gender": ["male", "female", "other", "unknown"]
    }
    res_cs_ok = validate_standalone_codings(
        {
            "resourceType": "Patient",
            "gender": {
                "system": "http://hl7.org/fhir/administrative-gender",
                "code": "female",
            },
        },
        TxOptions("local"),
        complete_systems=complete_cs,
    )
    assert res_cs_ok.errors == []

    res_cs_err = validate_standalone_codings(
        {
            "resourceType": "Patient",
            "gender": {
                "system": "http://hl7.org/fhir/administrative-gender",
                "code": "not-a-gender",
            },
        },
        TxOptions("local"),
        complete_systems=complete_cs,
    )
    assert len(res_cs_err.errors) == 1
    assert "not defined in CodeSystem" in res_cs_err.errors[0]

    # List of codings & remote standalone validation
    res_list_codings = validate_standalone_codings(
        {
            "resourceType": "Observation",
            "code": {
                "coding": [
                    {
                        "system": "http://hl7.org/fhir/administrative-gender",
                        "code": "unknown",
                    }
                ]
            },
        },
        TxOptions("local"),
        complete_systems=complete_cs,
    )
    assert res_list_codings.errors == []


def test_validate_standalone_remote_external_system() -> None:
    # Standalone coding with LOINC in remote mode
    opt_remote = TxOptions(mode="remote")
    _L1_CACHE[("https://tx.fhir.org/r4", "http://loinc.org", "883-9", "")] = (True, "Valid")
    _L1_CACHE[("https://tx.fhir.org/r4", "http://loinc.org", "000-0", "")] = (False, "Invalid")

    res_ok = validate_standalone_codings(
        {
            "resourceType": "Observation",
            "code": {"system": "http://loinc.org", "code": "883-9"},
        },
        opt_remote,
    )
    assert res_ok.errors == []
    assert res_ok.warnings == []

    res_err = validate_standalone_codings(
        {
            "resourceType": "Observation",
            "code": {"system": "http://loinc.org", "code": "000-0"},
        },
        opt_remote,
    )
    assert len(res_err.errors) == 1
    assert "is not valid in CodeSystem" in res_err.errors[0]

    with patch(
        "fhirlance.terminology.validate_remote_code",
        return_value=(None, "Down"),
    ):
        res_warn = validate_standalone_codings(
            {
                "resourceType": "Observation",
                "code": {"system": "http://loinc.org", "code": "fail-code"},
            },
            opt_remote,
        )
        assert len(res_warn.warnings) == 1
        assert "could not validate code" in res_warn.warnings[0]
