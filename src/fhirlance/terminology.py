"""Terminology validation runtime and remote cache for FHIR R4.

Supports offline grammar validation for UCUM, BCP-47, MIME, and ISO-3166,
local/complete CodeSystem lookups, and remote terminology servers (e.g. tx.fhir.org)
with two-tier L1 in-memory and L2 SQLite WAL caching.
"""

from __future__ import annotations

import contextlib
import dataclasses
import json
import os
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from fhirlance.profiles import COMPLETE_CODE_SYSTEMS

DEFAULT_TX_SERVER = "https://tx.fhir.org/r4"

_OFF_STRINGS = frozenset({"off", "n/a", "na", "none", "false", "0"})
_LOCAL_STRINGS = frozenset({"local", "on", "true", "1"})


@dataclass(frozen=True, slots=True)
class TxOptions:
    """Runtime terminology validation options."""

    mode: Literal["local", "remote", "off"] = "local"
    server: str = DEFAULT_TX_SERVER
    strict_extensible: bool = False
    cache_path: Path | None = None
    timeout: float = 5.0


@dataclass(frozen=True, slots=True)
class TerminologyResult:
    """Outcome of terminology validation containing errors and warnings."""

    errors: list[str]
    warnings: list[str]


@dataclass(frozen=True, slots=True)
class _TxCacheKey:
    server: str
    system: str
    code: str
    value_set_url: str


@dataclass(frozen=True, slots=True)
class _BindingContext:
    path: str
    vs_url: str
    strength: str
    options: TxOptions
    vs_spec: dict[str, Any] | None
    profile_prefix: str


@dataclass(frozen=True, slots=True)
class _StandaloneContext:
    options: TxOptions
    complete_systems: Mapping[str, frozenset[str]] | None


_DEFAULT_FROZEN_COMPLETE_SYSTEMS: dict[str, frozenset[str]] = {
    k: frozenset(v) for k, v in COMPLETE_CODE_SYSTEMS.items()
}


def _get_frozen_complete_systems(
    systems: Mapping[str, Collection[str]] | None,
) -> Mapping[str, frozenset[str]] | None:
    if systems is None:
        return None
    if systems is COMPLETE_CODE_SYSTEMS:
        return _DEFAULT_FROZEN_COMPLETE_SYSTEMS
    return {k: (v if isinstance(v, frozenset) else frozenset(v)) for k, v in systems.items()}


def _resolve_tx_mode_and_server(
    tx: str | bool | None,
) -> tuple[Literal["local", "remote", "off"], str]:
    if tx is False:
        return "off", DEFAULT_TX_SERVER
    if tx is True or tx is None:
        return "local", DEFAULT_TX_SERVER
    if isinstance(tx, str):
        cleaned = tx.strip()
        lower = cleaned.lower()
        if lower in _OFF_STRINGS:
            return "off", DEFAULT_TX_SERVER
        if lower in _LOCAL_STRINGS:
            return "local", DEFAULT_TX_SERVER
        if lower == "remote":
            return "remote", DEFAULT_TX_SERVER
        if cleaned.startswith(("http://", "https://")):
            return "remote", cleaned.rstrip("/")
    raise ValueError(f"Unsupported terminology mode or server URL: {tx!r}")


def parse_tx_options(
    tx: TxOptions | str | bool | None = "local",
    *,
    strict_extensible: bool = False,
    cache_path: Path | None = None,
) -> TxOptions:
    """Parse terminology options from string, boolean, or existing TxOptions."""
    if isinstance(tx, TxOptions):
        new_strict = tx.strict_extensible or strict_extensible
        new_path = cache_path if cache_path is not None else tx.cache_path
        return dataclasses.replace(tx, strict_extensible=new_strict, cache_path=new_path)
    mode, server = _resolve_tx_mode_and_server(tx)
    return TxOptions(
        mode=mode,
        server=server,
        strict_extensible=strict_extensible,
        cache_path=cache_path,
    )


# -----------------------------------------------------------------------------
# 1. ISO-3166 Country & Subdivision Codes
# -----------------------------------------------------------------------------

_ISO_3166_1_ALPHA2 = frozenset(
    {
        "AD",
        "AE",
        "AF",
        "AG",
        "AI",
        "AL",
        "AM",
        "AO",
        "AQ",
        "AR",
        "AS",
        "AT",
        "AU",
        "AW",
        "AX",
        "AZ",
        "BA",
        "BB",
        "BD",
        "BE",
        "BF",
        "BG",
        "BH",
        "BI",
        "BJ",
        "BL",
        "BM",
        "BN",
        "BO",
        "BQ",
        "BR",
        "BS",
        "BT",
        "BV",
        "BW",
        "BY",
        "BZ",
        "CA",
        "CC",
        "CD",
        "CF",
        "CG",
        "CH",
        "CI",
        "CK",
        "CL",
        "CM",
        "CN",
        "CO",
        "CR",
        "CU",
        "CV",
        "CW",
        "CX",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DM",
        "DO",
        "DZ",
        "EC",
        "EE",
        "EG",
        "EH",
        "ER",
        "ES",
        "ET",
        "FI",
        "FJ",
        "FK",
        "FM",
        "FO",
        "FR",
        "GA",
        "GB",
        "GD",
        "GE",
        "GF",
        "GG",
        "GH",
        "GI",
        "GL",
        "GM",
        "GN",
        "GP",
        "GQ",
        "GR",
        "GS",
        "GT",
        "GU",
        "GW",
        "GY",
        "HK",
        "HM",
        "HN",
        "HR",
        "HT",
        "HU",
        "ID",
        "IE",
        "IL",
        "IM",
        "IN",
        "IO",
        "IQ",
        "IR",
        "IS",
        "IT",
        "JE",
        "JM",
        "JO",
        "JP",
        "KE",
        "KG",
        "KH",
        "KI",
        "KM",
        "KN",
        "KP",
        "KR",
        "KW",
        "KY",
        "KZ",
        "LA",
        "LB",
        "LC",
        "LI",
        "LK",
        "LR",
        "LS",
        "LT",
        "LU",
        "LV",
        "LY",
        "MA",
        "MC",
        "MD",
        "ME",
        "MF",
        "MG",
        "MH",
        "MK",
        "ML",
        "MM",
        "MN",
        "MO",
        "MP",
        "MQ",
        "MR",
        "MS",
        "MT",
        "MU",
        "MV",
        "MW",
        "MX",
        "MY",
        "MZ",
        "NA",
        "NC",
        "NE",
        "NF",
        "NG",
        "NI",
        "NL",
        "NO",
        "NP",
        "NR",
        "NU",
        "NZ",
        "OM",
        "PA",
        "PE",
        "PF",
        "PG",
        "PH",
        "PK",
        "PL",
        "PM",
        "PN",
        "PR",
        "PS",
        "PT",
        "PW",
        "PY",
        "QA",
        "RE",
        "RO",
        "RS",
        "RU",
        "RW",
        "SA",
        "SB",
        "SC",
        "SD",
        "SE",
        "SG",
        "SH",
        "SI",
        "SJ",
        "SK",
        "SL",
        "SM",
        "SN",
        "SO",
        "SR",
        "SS",
        "ST",
        "SV",
        "SX",
        "SY",
        "SZ",
        "TC",
        "TD",
        "TF",
        "TG",
        "TH",
        "TJ",
        "TK",
        "TL",
        "TM",
        "TN",
        "TO",
        "TR",
        "TT",
        "TV",
        "TW",
        "TZ",
        "UA",
        "UG",
        "UM",
        "US",
        "UY",
        "UZ",
        "VA",
        "VC",
        "VE",
        "VG",
        "VI",
        "VN",
        "VU",
        "WF",
        "WS",
        "YE",
        "YT",
        "ZA",
        "ZM",
        "ZW",
    }
)
_ISO_3166_2_RE = re.compile(r"^[A-Z]{2}-[A-Z0-9]{1,3}$")
_ISO_3166_ALPHA3_OR_NUM_RE = re.compile(r"^([A-Z]{3}|\d{3})$")
_ISO_3166_ALPHA2_LEN = 2


def is_valid_iso3166_code(code: str, system: str = "urn:iso:std:iso:3166") -> bool:
    """Validate ISO-3166-1 or ISO-3166-2 country/subdivision code."""
    if not code or not isinstance(code, str):
        return False
    trimmed = code.strip()
    if trimmed != code:
        return False
    if system.endswith(":-2") or system.endswith("-2") or "-" in code:
        if not _ISO_3166_2_RE.match(code):
            return False
        country = code.split("-", 1)[0]
        return country in _ISO_3166_1_ALPHA2
    if len(code) == _ISO_3166_ALPHA2_LEN:
        return code in _ISO_3166_1_ALPHA2
    return bool(_ISO_3166_ALPHA3_OR_NUM_RE.match(code))


_ISO_4217_RE = re.compile(r"^[A-Z]{3}$")


def is_valid_iso4217_code(code: str) -> bool:
    """Validate ISO-4217 3-letter currency code."""
    return bool(code and _ISO_4217_RE.match(code))


# -----------------------------------------------------------------------------
# 2. MIME Types (urn:ietf:bcp:13)
# -----------------------------------------------------------------------------

_MIME_RE = re.compile(
    r"^(?:application|audio|example|font|image|message|model|multipart|text|video|chemical"
    r"|x-[a-zA-Z0-9!#$%&'*+^_`|~-]+)/[a-zA-Z0-9!#$%&'*+^_`|~.-]+"
    r"(?:\s*;\s*[a-zA-Z0-9!#$%&'*+^_`|~-]+=(?:[a-zA-Z0-9!#$%&'*+^_`|~.-]+|\"[^\"]*\"))*$",
    re.IGNORECASE,
)


def is_valid_mime_code(code: str) -> bool:
    """Validate RFC 2045 / RFC 6838 MIME media type."""
    if not code or not isinstance(code, str):
        return False
    trimmed = code.strip()
    if trimmed != code or " " in trimmed.split(";", 1)[0]:
        return False
    return bool(_MIME_RE.match(trimmed))


# -----------------------------------------------------------------------------
# 3. BCP-47 Language Tags (urn:ietf:bcp:47)
# -----------------------------------------------------------------------------

_BCP47_RE = re.compile(
    r"^("
    r"(?:i-[a-z]+|x-[a-z0-9]{1,8}(?:-[a-z0-9]{1,8})*|"
    r"en-GB-oed|i-ami|i-bnn|i-default|i-enochian|i-hak|i-klingon|i-lux|i-mingo|i-navajo|"
    r"i-pwn|i-tao|i-tay|i-tsu|sgn-BE-FR|sgn-BE-NL|sgn-CH-DE|art-lojban|cel-gaulish|no-bok|"
    r"no-nyn|zh-guoyu|zh-hakka|zh-min|zh-min-nan|zh-xiang)"
    r"|"
    r"(?:[a-zA-Z]{2,3}(?:-[a-zA-Z]{3}){0,3}|[a-zA-Z]{4,8})"
    r"(?:-[a-zA-Z]{4})?"
    r"(?:-[a-zA-Z]{2}|-[0-9]{3})?"
    r"(?:-[a-zA-Z0-9]{5,8}|-[0-9][a-zA-Z0-9]{3})*"
    r"(?:-[0-9a-wy-zA-WY-Z](?:-[a-zA-Z0-9]{2,8})+)*"
    r"(?:-x(?:-[a-zA-Z0-9]{1,8})+)*"
    r")$",
    re.IGNORECASE,
)


def is_valid_bcp47_code(code: str) -> bool:
    """Validate RFC 5646 BCP-47 language tag."""
    if not code or not isinstance(code, str):
        return False
    trimmed = code.strip()
    if trimmed != code or " " in trimmed:
        return False
    return bool(_BCP47_RE.match(trimmed))


# -----------------------------------------------------------------------------
# 4. UCUM Units of Measure (http://unitsofmeasure.org)
# -----------------------------------------------------------------------------

_UCUM_PREFIXES = (
    "Ki",
    "Mi",
    "Gi",
    "Ti",
    "da",
    "Y",
    "Z",
    "E",
    "P",
    "T",
    "G",
    "M",
    "k",
    "h",
    "d",
    "c",
    "m",
    "u",
    "n",
    "p",
    "f",
    "a",
    "z",
    "y",
)

_UCUM_ATOMS = frozenset(
    {
        "m",
        "g",
        "s",
        "A",
        "K",
        "mol",
        "cd",
        "rad",
        "sr",
        "Hz",
        "N",
        "Pa",
        "J",
        "W",
        "C",
        "V",
        "F",
        "Ohm",
        "S",
        "Wb",
        "T",
        "H",
        "Cel",
        "lm",
        "lx",
        "Bq",
        "Gy",
        "Sv",
        "kat",
        "l",
        "L",
        "ar",
        "min",
        "h",
        "d",
        "wk",
        "mo",
        "a",
        "t",
        "u",
        "eV",
        "B",
        "Oct",
        "bit",
        "Bd",
        "osm",
        "eq",
        "Eq",
        "g%",
        "U",
        "st",
        "Ci",
        "R",
        "Gal",
        "P",
        "St",
        "b",
        "atm",
        "att",
        "bar",
        "cal",
        "erg",
        "gf",
        "ky",
        "lbf",
        "sb",
        "ph",
        "poise",
        "rem",
        "sphi",
        "sph",
        "torr",
        "1",
        "%",
    }
)

_BRACKETED_UNITS = frozenset(
    {
        "[in_i]",
        "[ft_i]",
        "[yd_i]",
        "[mi_i]",
        "[lb_av]",
        "[oz_av]",
        "[dr_av]",
        "[gr]",
        "[degF]",
        "[gal_us]",
        "[qt_us]",
        "[pt_us]",
        "[foz_us]",
        "[cup_us]",
        "[tbs_us]",
        "[tsp_us]",
        "[IU]",
        "[iU]",
        "[arb'U]",
        "[pH]",
        "[drop]",
        "[sft_i]",
        "[sin_i]",
        "[cin_i]",
        "[cft_i]",
        "[PRU]",
        "[wood'U]",
        "[diop]",
        "[mesh_i]",
        "[Ch]",
        "[USP'U]",
        "[GPL'U]",
        "[MPL'U]",
        "[APL'U]",
        "[beth'U]",
        "[todd'U]",
        "[bdsk'U]",
        "[knk'U]",
        "[mclg'U]",
        "[tb'U]",
        "[CCID_50]",
        "[TCID_50]",
        "[PFU]",
        "[CFU]",
        "[FFU]",
        "[Lf]",
        "[hp_X]",
        "[hp_C]",
        "[hp_M]",
        "[hp_Q]",
        "[kp_C]",
        "[acr_us]",
        "[stone_av]",
        "[cwt_av]",
        "[lton_av]",
        "[ston_av]",
        "[pnt_us]",
        "[line]",
        "[point]",
        "[mil_i]",
        "[cal_th]",
        "[cal_IT]",
        "[degRe]",
        "[in_us]",
        "[rd_us]",
        "[ch_us]",
        "[lk_us]",
        "[fth_us]",
        "[fur_us]",
        "[nmi_i]",
        "[kn_i]",
        "[dpt]",
        "[AU]",
        "[pc]",
        "[ly]",
        "[ppth]",
        "[ppm]",
        "[ppb]",
        "[tr]",
        "[Hg]",
        "[H2O]",
    }
)

_PRESSURE_UNITS = frozenset(
    {
        "mm[Hg]",
        "cm[Hg]",
        "m[Hg]",
        "mm[H2O]",
        "cm[H2O]",
        "m[H2O]",
        "um[Hg]",
        "um[H2O]",
    }
)

_NUMERIC_ATOM_RE = re.compile(r"^(?:10\*(?:[+-]?\d+)|10\^(?:[+-]?\d+)|\d+)$")
_EXPONENT_RE = re.compile(r"^(.+?)([+-]?\d+)$")


def _is_valid_atom_or_prefixed(atom: str) -> bool:
    if atom in _UCUM_ATOMS:
        return True
    for prefix in _UCUM_PREFIXES:
        if atom.startswith(prefix) and atom[len(prefix) :] in _UCUM_ATOMS:
            return True
    return False


def _is_bracketed_with_exponent(token: str) -> bool:
    if token in _BRACKETED_UNITS:
        return True
    if "]" in token and not token.endswith("]"):
        b_idx = token.rfind("]")
        base = token[: b_idx + 1]
        exp = token[b_idx + 1 :]
        if base in _BRACKETED_UNITS and (exp.isdigit() or (exp[0] in "+-" and exp[1:].isdigit())):
            return True
    return False


def _is_valid_ucum_leaf(token: str) -> bool:
    if not token:
        return False
    if token.endswith("}") and "{" in token:
        idx = token.find("{")
        annot = token[idx + 1 : -1]
        if "{" in annot or "}" in annot:
            return False
        if idx == 0:
            return True
        token = token[:idx]

    if token in _PRESSURE_UNITS or _is_bracketed_with_exponent(token):
        return True
    if _NUMERIC_ATOM_RE.match(token):
        return True

    match = _EXPONENT_RE.match(token)
    if match and not token.startswith("["):
        token = match.group(1)

    return _is_valid_atom_or_prefixed(token)


def _consume_delimited(
    s: str, start: int, close_ch: str, forbidden: tuple[str, ...]
) -> tuple[str, int] | None:
    n = len(s)
    i = start + 1
    while i < n and s[i] != close_ch:
        if s[i] in forbidden:
            return None
        i += 1
    if i >= n:
        return None
    return s[start : i + 1], i + 1


def _tokenize_ucum(s: str) -> list[str] | None:
    tokens: list[str] = []
    i = 0
    n = len(s)
    current: list[str] = []
    while i < n:
        ch = s[i]
        if ch in ("(", ")", ".", "/"):
            if current:
                tokens.append("".join(current))
                current = []
            tokens.append(ch)
            i += 1
        elif ch == "{":
            res = _consume_delimited(s, i, "}", ("{",))
            if res is None:
                return None
            seg, i = res
            current.append(seg)
        elif ch == "[":
            res = _consume_delimited(s, i, "]", ("[", "{", "}"))
            if res is None:
                return None
            seg, i = res
            current.append(seg)
        elif ch.isspace():
            return None
        else:
            current.append(ch)
            i += 1
    if current:
        tokens.append("".join(current))
    return tokens


def _is_exponent_token(token: str) -> bool:
    return bool(token and (token.isdigit() or (token[0] in "+-" and token[1:].isdigit())))


def _parse_ucum_term(tokens: list[str], idx: int) -> tuple[int, bool]:
    if idx >= len(tokens):
        return idx, False
    tok = tokens[idx]
    if tok == "(":
        next_idx, ok = _parse_ucum_expr(tokens, idx + 1)
        if not ok or next_idx >= len(tokens) or tokens[next_idx] != ")":
            return next_idx, False
        next_idx += 1
        if next_idx < len(tokens) and _is_exponent_token(tokens[next_idx]):
            next_idx += 1
        return next_idx, True
    if _is_valid_ucum_leaf(tok):
        return idx + 1, True
    return idx, False


def _parse_ucum_expr(tokens: list[str], idx: int) -> tuple[int, bool]:
    idx, ok = _parse_ucum_term(tokens, idx)
    if not ok:
        return idx, False
    while idx < len(tokens) and tokens[idx] in (".", "/"):
        idx += 1
        idx, ok = _parse_ucum_term(tokens, idx)
        if not ok:
            return idx, False
    return idx, True


def _parse_ucum_tokens(tokens: list[str]) -> bool:
    if not tokens:
        return False
    if tokens[0] == "/":
        tokens = ["1", *tokens]
    idx, ok = _parse_ucum_expr(tokens, 0)
    return ok and idx == len(tokens)


def is_valid_ucum_code(code: str) -> bool:
    """Validate UCUM metric, customary, and clinical unit expressions."""
    if not code or not isinstance(code, str):
        return False
    tokens = _tokenize_ucum(code)
    if tokens is None:
        return False
    return _parse_ucum_tokens(tokens)


# -----------------------------------------------------------------------------
# 5. Remote Terminology Client & Two-Tier Caching
# -----------------------------------------------------------------------------

_L1_CACHE: dict[tuple[str, str, str, str], tuple[bool, str | None]] = {}

_REMOTE_EXTERNAL_SYSTEMS = frozenset(
    {
        "http://snomed.info/sct",
        "http://loinc.org",
        "http://www.nlm.nih.gov/research/umls/rxnorm",
        "http://hl7.org/fhir/sid/icd-10-cm",
        "http://hl7.org/fhir/sid/icd-10",
        "http://www.ama-assn.org/go/cpt",
        "http://www.whocc.no/atc",
    }
)


def _default_cache_db_path() -> Path:
    return Path.home() / ".fhir" / "fhirlance-tx-cache.sqlite"


_INITIALIZED_SQLITE_PATHS: set[tuple[int, Path]] = set()


def _init_sqlite_cache(path: Path) -> sqlite3.Connection | None:
    try:
        resolved_path = path.resolve()
        proc_key = (os.getpid(), resolved_path)
        if proc_key in _INITIALIZED_SQLITE_PATHS and path.exists():
            return sqlite3.connect(str(path), timeout=5.0)

        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tx_cache (
                server TEXT NOT NULL,
                system TEXT NOT NULL,
                code TEXT NOT NULL,
                value_set_url TEXT NOT NULL,
                result INTEGER NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (server, system, code, value_set_url)
            );
            """
        )
        _INITIALIZED_SQLITE_PATHS.add(proc_key)
    except (sqlite3.Error, OSError):
        return None
    else:
        return conn


def _read_sqlite_cache(path: Path, key: _TxCacheKey) -> tuple[bool, str | None] | None:
    conn = _init_sqlite_cache(path)
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT result, message FROM tx_cache
            WHERE server = ? AND system = ? AND code = ? AND value_set_url = ?
            LIMIT 1;
            """,
            (key.server, key.system, key.code, key.value_set_url),
        )
        row = cur.fetchone()
        if row is not None:
            return bool(row[0]), row[1]
    except (sqlite3.Error, OSError):
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()
    return None


def _write_sqlite_cache(path: Path, key: _TxCacheKey, result: bool, message: str | None) -> None:
    conn = _init_sqlite_cache(path)
    if conn is None:
        return
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO tx_cache (server, system, code, value_set_url, result, message)
            VALUES (?, ?, ?, ?, ?, ?);
            """,
            (key.server, key.system, key.code, key.value_set_url, int(result), message),
        )
        conn.commit()
    except (sqlite3.Error, OSError):
        pass
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()


def _build_remote_url(server: str, system: str, code: str, vs_url: str | None) -> str:
    if vs_url:
        params = urllib.parse.urlencode({"url": vs_url, "system": system, "code": code})
        return f"{server}/ValueSet/$validate-code?{params}"
    params = urllib.parse.urlencode({"url": system, "code": code})
    return f"{server}/CodeSystem/$validate-code?{params}"


def _parse_parameters_response(data: dict[str, Any]) -> tuple[bool | None, str | None]:
    result: bool | None = None
    message: str | None = None
    for param in data.get("parameter", []):
        if not isinstance(param, dict):
            continue
        p_name = param.get("name")
        if p_name == "result":
            result = param.get("valueBoolean")
        elif p_name == "message":
            message = param.get("valueString")
    return result, message


def _execute_remote_call(url: str, timeout: float) -> tuple[bool | None, str | None]:
    if not url.startswith(("http://", "https://")):
        return False, f"Invalid URL scheme: {url}"
    req = urllib.request.Request(  # noqa: S310
        url,
        headers={"Accept": "application/fhir+json, application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict):
                return _parse_parameters_response(payload)
            return None, "Unexpected non-dict response from terminology server"
    except urllib.error.HTTPError as exc:
        try:
            err_data = json.loads(exc.read().decode("utf-8"))
            if isinstance(err_data, dict):
                res, msg = _parse_parameters_response(err_data)
                if res is not None:
                    return res, msg
        except (OSError, json.JSONDecodeError):
            pass
        return None, f"Terminology server HTTP {exc.code}: {exc.reason}"
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return None, f"Terminology server unreachable: {exc}"


def validate_remote_code(
    *,
    options: TxOptions,
    system: str,
    code: str,
    value_set_url: str | None = None,
) -> tuple[bool | None, str | None]:
    """Validate a code remotely with L1 in-memory and L2 SQLite caching."""
    if options.mode != "remote":
        return None, None

    vs_url = value_set_url or ""
    cache_key = (options.server, system, code, vs_url)
    if cache_key in _L1_CACHE:
        return _L1_CACHE[cache_key]

    cache_path = options.cache_path or _default_cache_db_path()
    t_key = _TxCacheKey(options.server, system, code, vs_url)
    l2_cached = _read_sqlite_cache(cache_path, t_key)
    if l2_cached is not None:
        _L1_CACHE[cache_key] = l2_cached
        return l2_cached

    url = _build_remote_url(options.server, system, code, value_set_url)
    res, msg = _execute_remote_call(url, options.timeout)
    if res is not None:
        _L1_CACHE[cache_key] = (res, msg)
        _write_sqlite_cache(cache_path, t_key, res, msg)
    return res, msg


class TxClient:
    """Two-tier remote terminology client with in-memory and SQLite caching."""

    def __init__(self, options: TxOptions | None = None) -> None:
        self.options = options or TxOptions()

    def validate_code(
        self, system: str, code: str, value_set_url: str | None = None
    ) -> tuple[bool | None, str | None]:
        """Validate code against a system or ValueSet remotely."""
        return validate_remote_code(
            options=self.options,
            system=system,
            code=code,
            value_set_url=value_set_url,
        )


# -----------------------------------------------------------------------------
# 6. ValueSet & Standalone Codings Evaluation
# -----------------------------------------------------------------------------


def _check_grammar_system(system: str, code: str) -> tuple[bool, bool]:
    if system == "http://unitsofmeasure.org":
        return True, is_valid_ucum_code(code)
    if system == "urn:ietf:bcp:47":
        return True, is_valid_bcp47_code(code)
    if system in ("urn:ietf:bcp:13", "http://hl7.org/fhir/ValueSet/mimetypes"):
        return True, is_valid_mime_code(code)
    if system.startswith("urn:iso:std:iso:3166"):
        return True, is_valid_iso3166_code(code, system)
    if system == "urn:iso:std:iso:4217":
        return True, is_valid_iso4217_code(code)
    return False, True


def _evaluate_external_code(
    system: str,
    code: str,
    vs_url: str,
    vs_spec: dict[str, Any] | None,
    options: TxOptions,
) -> tuple[bool | None, str | None]:
    if vs_spec is None:
        return True, None
    ext = vs_spec.get("external_systems", ())
    if system in ext or "*" in ext:
        if code in vs_spec.get("codes", ()):
            return True, None
        if options.mode == "remote":
            return validate_remote_code(
                options=options, system=system, code=code, value_set_url=vs_url
            )
        return True, None
    return False, None


def _evaluate_grammar_in_valueset(
    system: str,
    code: str,
    valid_grammar: bool,
    vs_spec: dict[str, Any] | None,
) -> tuple[bool | None, str | None]:
    if not valid_grammar:
        return False, f"Invalid code '{code}' in grammar system '{system}'"
    if vs_spec is None:
        return True, None
    sys_codes = vs_spec.get("system_codes", {})
    ext = vs_spec.get("external_systems", ())
    if system in sys_codes:
        return (code in sys_codes[system]), None
    if system in ext or "*" in ext:
        return True, None
    if vs_spec.get("codes"):
        return (code in vs_spec["codes"]), None
    return True, None


def _evaluate_plain_code_in_valueset(
    code: str,
    vs_spec: dict[str, Any],
) -> tuple[bool | None, str | None] | None:
    sys_codes = vs_spec.get("system_codes", {})
    if code in vs_spec.get("codes", ()) or any(code in c for c in sys_codes.values()):
        return True, None
    ext = vs_spec.get("external_systems", ())
    if ext:
        grammar_checks = [_check_grammar_system(s, code) for s in ext]
        if any(is_g and valid for is_g, valid in grammar_checks):
            return True, None
        all_grammar = bool(grammar_checks) and all(is_g for is_g, _ in grammar_checks)
        if all_grammar and not vs_spec.get("codes") and not sys_codes:
            return False, f"Invalid code '{code}'"
    if sys_codes or vs_spec.get("codes"):
        return False, None
    return None


def _evaluate_code_in_valueset(
    system: str,
    code: str,
    vs_url: str,
    vs_spec: dict[str, Any] | None,
    options: TxOptions,
) -> tuple[bool | None, str | None]:
    is_grammar, valid_grammar = _check_grammar_system(system, code)
    if is_grammar:
        return _evaluate_grammar_in_valueset(system, code, valid_grammar, vs_spec)

    if vs_spec is not None:
        if system:
            sys_codes = vs_spec.get("system_codes", {})
            if system in sys_codes:
                return (code in sys_codes[system]), None
        else:
            plain_res = _evaluate_plain_code_in_valueset(code, vs_spec)
            if plain_res is not None:
                return plain_res

    return _evaluate_external_code(system, code, vs_url, vs_spec, options)


def _record_binding_issue(
    system: str,
    code: str,
    res: bool | None,
    msg: str | None,
    ctx: _BindingContext,
) -> tuple[list[str], list[str]]:
    if res is True:
        return [], []
    if res is None:
        return [], [f"{ctx.profile_prefix}'{ctx.path}': could not validate code '{code}' ({msg})"]
    prefix = ctx.profile_prefix
    if ctx.strength == "required":
        return [f"{prefix}'{ctx.path}' code '{code}' not in required ValueSet '{ctx.vs_url}'"], []
    if ctx.strength == "extensible":
        is_known = (
            ctx.vs_spec is not None
            and bool(ctx.vs_spec.get("system_codes"))
            and system in ctx.vs_spec.get("system_codes", {})
        )
        msg_str = f"{prefix}'{ctx.path}' code '{code}' not in extensible ValueSet '{ctx.vs_url}'"
        if is_known or ctx.options.strict_extensible:
            return [msg_str], []
        return [], [msg_str]
    return [], []


def _validate_codings_list(
    codings: list[Any],
    ctx: _BindingContext,
) -> tuple[list[str], list[str]]:
    results: list[tuple[bool | None, str | None, str, str]] = []
    for c in codings:
        if isinstance(c, dict) and "code" in c and isinstance(c["code"], str) and c["code"]:
            c_sys = str(c.get("system") or "")
            c_code = c["code"]
            r, m = _evaluate_code_in_valueset(c_sys, c_code, ctx.vs_url, ctx.vs_spec, ctx.options)
            results.append((r, m, c_sys, c_code))

    if not results:
        if ctx.strength == "required":
            msg = (
                f"{ctx.profile_prefix}'{ctx.path}' has no coding "
                f"for required ValueSet '{ctx.vs_url}'"
            )
            return [msg], []
        return [], []

    if any(r is True for r, _, _, _ in results):
        return [], []

    none_entry = next(((r, m, s, c) for r, m, s, c in results if r is None), None)
    if none_entry is not None:
        _, first_warn, _, c_repr = none_entry
        warn_msg = (
            f"{ctx.profile_prefix}'{ctx.path}': could not validate code '{c_repr}' ({first_warn})"
        )
        return [], [warn_msg]

    sys_codes = (ctx.vs_spec or {}).get("system_codes", {})
    known_entry = next(((r, m, s, c) for r, m, s, c in results if s in sys_codes), None)
    chosen = known_entry if known_entry is not None else results[0]
    _, _, c_sys, c_repr = chosen
    return _record_binding_issue(c_sys, c_repr, False, None, ctx)


def _validate_codeable_concept(
    val: dict[str, Any],
    ctx: _BindingContext,
) -> tuple[list[str], list[str]]:
    if not val:
        return [], []
    codings = val.get("coding")
    if isinstance(codings, list) and codings:
        return _validate_codings_list(codings, ctx)

    if ctx.strength == "required":
        if val.get("text"):
            text_repr = str(val.get("text") or "")
            return [
                f"{ctx.profile_prefix}'{ctx.path}' code '{text_repr}' "
                f"not in required ValueSet '{ctx.vs_url}'"
            ], []
        return [
            f"{ctx.profile_prefix}'{ctx.path}' has no coding for required ValueSet '{ctx.vs_url}'"
        ], []
    return [], []


def _validate_one_binding_value(
    val: Any,
    ctx: _BindingContext,
) -> tuple[list[str], list[str]]:
    if isinstance(val, str):
        res, msg = _evaluate_code_in_valueset("", val, ctx.vs_url, ctx.vs_spec, ctx.options)
        return _record_binding_issue("", val, res, msg, ctx)
    if isinstance(val, dict):
        if "code" in val and isinstance(val["code"], str):
            code_repr = val["code"]
            system = str(val.get("system") or "")
            res, msg = _evaluate_code_in_valueset(
                system, code_repr, ctx.vs_url, ctx.vs_spec, ctx.options
            )
            return _record_binding_issue(system, code_repr, res, msg, ctx)
        return _validate_codeable_concept(val, ctx)
    return [], []


def _normalize_vs_spec(vs_spec: Any) -> dict[str, Any] | None:
    if isinstance(vs_spec, dict):
        codes = vs_spec.get("codes")
        sys_codes = vs_spec.get("system_codes")
        codes_ok = codes is None or isinstance(codes, frozenset)
        sys_ok = not isinstance(sys_codes, dict) or all(
            isinstance(v, frozenset) for v in sys_codes.values()
        )
        if codes_ok and sys_ok:
            return vs_spec
        normalized = dict(vs_spec)
        if codes is not None and not isinstance(codes, frozenset):
            normalized["codes"] = frozenset(codes)
        if isinstance(sys_codes, dict):
            normalized["system_codes"] = {
                k: (v if isinstance(v, frozenset) else frozenset(v)) for k, v in sys_codes.items()
            }
        return normalized
    if isinstance(vs_spec, (list, set, tuple, frozenset)):
        return {"codes": frozenset(vs_spec)}
    return None


def validate_binding_value(
    val: Any,
    path: str,
    vs_url: str,
    strength: str,
    options: TxOptions,
    **kwargs: Any,
) -> TerminologyResult:
    """Validate a bound element value against a ValueSet."""
    if options.mode == "off" or val is None:
        return TerminologyResult(errors=[], warnings=[])

    raw_spec = kwargs.get("vs_spec")
    vs_spec = _normalize_vs_spec(raw_spec)
    prefix = str(kwargs.get("profile_prefix", ""))
    ctx = _BindingContext(
        path=path,
        vs_url=vs_url,
        strength=strength.lower(),
        options=options,
        vs_spec=vs_spec,
        profile_prefix=prefix,
    )

    if isinstance(val, list):
        errors: list[str] = []
        warnings: list[str] = []
        for item in val:
            errs, warns = _validate_one_binding_value(item, ctx)
            errors.extend(errs)
            warnings.extend(warns)
        return TerminologyResult(errors=errors, warnings=warnings)

    errs, warns = _validate_one_binding_value(val, ctx)
    return TerminologyResult(errors=errs, warnings=warns)


def _format_trail_path(trail: list[tuple[int, str | int]], idx: int) -> str:
    segs: list[str] = []
    while idx > 0:
        parent_idx, seg = trail[idx]
        segs.append(f"[{seg}]" if isinstance(seg, int) else f".{seg}")
        idx = parent_idx
    segs.append(str(trail[0][1]))
    segs.reverse()
    return "".join(segs)


def _subtree_has_extension_key(root: dict[str, Any]) -> bool:
    stack: list[Any] = [root]
    while stack:
        curr = stack.pop()
        if isinstance(curr, dict):
            for k, v in curr.items():
                if k in ("extension", "modifierExtension") or (len(k) > 1 and k[0] == "_"):
                    return True
                if isinstance(v, (dict, list)):
                    stack.append(v)
        elif isinstance(curr, list):
            stack.extend(item for item in curr if isinstance(item, (dict, list)))
    return False


def _scan_codings_and_extensions(
    resource: dict[str, Any],
    root_path: str,
) -> tuple[list[tuple[int, str, str]], list[tuple[int, str | int]], bool]:
    trail: list[tuple[int, str | int]] = [(-1, root_path)]
    stack: list[tuple[int, Any]] = [(0, resource)]
    items: list[tuple[int, str, str]] = []
    has_extensions = False

    while stack:
        node_idx, node = stack.pop()
        if isinstance(node, dict):
            if node is not resource and isinstance(node.get("resourceType"), str):
                has_extensions = has_extensions or _subtree_has_extension_key(node)
                continue
            if (
                "url" not in node
                and isinstance(node.get("system"), str)
                and isinstance(node.get("code"), str)
            ):
                items.append((node_idx, node["system"], node["code"]))
            for k, v in reversed(node.items()):
                if k in ("extension", "modifierExtension") or (len(k) > 1 and k[0] == "_"):
                    has_extensions = True
                if isinstance(v, (dict, list)):
                    child_idx = len(trail)
                    trail.append((node_idx, k))
                    stack.append((child_idx, v))
        else:
            for i in range(len(node) - 1, -1, -1):
                item = node[i]
                if isinstance(item, (dict, list)):
                    child_idx = len(trail)
                    trail.append((node_idx, i))
                    stack.append((child_idx, item))

    return items, trail, has_extensions


def _check_standalone_item(
    node_idx: int,
    trail: list[tuple[int, str | int]],
    system: str,
    code: str,
    ctx: _StandaloneContext,
) -> tuple[str | None, str | None]:
    is_grammar, valid_grammar = _check_grammar_system(system, code)
    if is_grammar:
        if valid_grammar:
            return None, None
        path = _format_trail_path(trail, node_idx)
        return (
            f"Terminology[{path}]: code '{code}' is not valid in grammar system '{system}'",
            None,
        )

    if ctx.complete_systems is not None and system in ctx.complete_systems:
        err = (
            None
            if code in ctx.complete_systems[system]
            else (
                f"Terminology[{_format_trail_path(trail, node_idx)}]: "
                f"code '{code}' is not defined in CodeSystem '{system}'"
            )
        )
        return err, None

    if ctx.options.mode == "remote" and system in _REMOTE_EXTERNAL_SYSTEMS:
        res, msg = validate_remote_code(options=ctx.options, system=system, code=code)
        if res is False:
            path = _format_trail_path(trail, node_idx)
            return (
                f"Terminology[{path}]: code '{code}' is not valid in CodeSystem '{system}'",
                None,
            )
        if res is None:
            path = _format_trail_path(trail, node_idx)
            return (
                None,
                f"Terminology[{path}]: could not validate code '{code}' on remote server ({msg})",
            )

    return None, None


def scan_and_validate_standalone_codings(
    resource: dict[str, Any],
    options: TxOptions,
    *,
    complete_systems: Mapping[str, Collection[str]] | None = None,
) -> tuple[TerminologyResult, bool]:
    """Scan a resource in a single pass for standalone Codings and extension keys."""
    if options.mode == "off":
        return TerminologyResult(errors=[], warnings=[]), False

    root_path = str(resource.get("resourceType") or "Resource")
    items, trail, has_extensions = _scan_codings_and_extensions(resource, root_path)

    frozen_systems = _get_frozen_complete_systems(complete_systems)
    ctx = _StandaloneContext(options=options, complete_systems=frozen_systems)
    errors: list[str] = []
    warnings: list[str] = []
    for node_idx, system, code in items:
        err, warn = _check_standalone_item(node_idx, trail, system, code, ctx)
        if err is not None:
            errors.append(err)
        if warn is not None:
            warnings.append(warn)

    lang = resource.get("language")
    if isinstance(lang, str) and not is_valid_bcp47_code(lang):
        errors.append(
            f"Terminology[{root_path}.language]: code '{lang}' is not valid "
            "in grammar system 'urn:ietf:bcp:47'"
        )

    return TerminologyResult(errors=errors, warnings=warnings), has_extensions


def validate_standalone_codings(
    resource: dict[str, Any],
    options: TxOptions,
    *,
    complete_systems: Mapping[str, Collection[str]] | None = None,
) -> TerminologyResult:
    """Recursively validate standalone Codings and Quantities against CodeSystems."""
    result, _ = scan_and_validate_standalone_codings(
        resource, options, complete_systems=complete_systems
    )
    return result
