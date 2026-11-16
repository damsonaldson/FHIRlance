"""FHIR R4 ConceptMap parsing, registry, and $translate evaluation."""

from __future__ import annotations

import contextlib
import json
import os
import sqlite3
import threading
import urllib.error
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fhirlance.terminology import TxClient

POSITIVE_EQUIVALENCES: frozenset[str] = frozenset(
    {
        "relatedto",
        "equivalent",
        "equal",
        "wider",
        "subsumes",
        "narrower",
        "specializes",
        "inexact",
    }
)
NEGATIVE_EQUIVALENCES: frozenset[str] = frozenset({"unmatched", "disjoint"})

_REVERSE_EQUIVALENCE: dict[str, str] = {
    "wider": "narrower",
    "narrower": "wider",
    "subsumes": "specializes",
    "specializes": "subsumes",
}

_TRANSLATE_LOCK = threading.Lock()
_TRANSLATE_L1_CACHE_MAX = 4096
_TRANSLATE_L1_CACHE: dict[tuple[str, ...], TranslateResult] = {}
_INITIALIZED_TRANSLATE_DB: set[tuple[int, Path]] = set()


@dataclass(frozen=True, slots=True)
class ConceptMapDependsOnSpec:
    """Dependency or product constraint on a ConceptMap target mapping."""

    property: str
    value: str
    system: str | None = None
    display: str | None = None


@dataclass(frozen=True, slots=True)
class ConceptMapTargetSpec:
    """Target mapping entry within a ConceptMap element."""

    equivalence: str
    code: str | None = None
    display: str | None = None
    comment: str | None = None
    depends_on: tuple[ConceptMapDependsOnSpec, ...] = ()
    product: tuple[ConceptMapDependsOnSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class ConceptMapElementSpec:
    """Source concept element within a ConceptMap group."""

    code: str
    display: str | None = None
    targets: tuple[ConceptMapTargetSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class ConceptMapUnmappedSpec:
    """Fallback behavior when a source code is not mapped in a group."""

    mode: str
    code: str | None = None
    display: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class ConceptMapGroupSpec:
    """Source-to-target system group within a ConceptMap."""

    source: str | None = None
    source_version: str | None = None
    target: str | None = None
    target_version: str | None = None
    elements: tuple[ConceptMapElementSpec, ...] = ()
    unmapped: ConceptMapUnmappedSpec | None = None


@dataclass(frozen=True, slots=True)
class ConceptMapSpec:
    """Parsed FHIR R4 ConceptMap specification."""

    url: str
    version: str | None = None
    name: str | None = None
    status: str | None = None
    source_uri: str | None = None
    target_uri: str | None = None
    groups: tuple[ConceptMapGroupSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class TranslateMatch:
    """Single positive concept translation match."""

    equivalence: str
    system: str | None = None
    code: str | None = None
    display: str | None = None
    comment: str | None = None
    source: str | None = None
    depends_on: tuple[ConceptMapDependsOnSpec, ...] = ()
    product: tuple[ConceptMapDependsOnSpec, ...] = ()


@dataclass(frozen=True, slots=True)
class TranslateRequest:
    """Input parameters for ConceptMap/$translate."""

    code: str
    system: str | None = None
    version: str | None = None
    url: str | None = None
    source: str | None = None
    target: str | None = None
    target_system: str | None = None
    reverse: bool = False
    depends_on: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True)
class TranslateResult:
    """Outcome of ConceptMap/$translate."""

    result: bool
    message: str | None = None
    matches: tuple[TranslateMatch, ...] = ()


def _opt_str(value: Any) -> str | None:
    return value if isinstance(value, str) and value else None


def _strip_version(uri: str | None) -> str | None:
    if uri is None:
        return None
    return uri.split("|", 1)[0]


def _parse_depends_on(raw_list: Any) -> tuple[ConceptMapDependsOnSpec, ...]:
    if not isinstance(raw_list, list):
        return ()
    items: list[ConceptMapDependsOnSpec] = []
    for entry in raw_list:
        if not isinstance(entry, dict):
            continue
        prop = _opt_str(entry.get("property"))
        val = _opt_str(entry.get("value"))
        if prop is None or val is None:
            continue
        items.append(
            ConceptMapDependsOnSpec(
                property=prop,
                value=val,
                system=_opt_str(entry.get("system")),
                display=_opt_str(entry.get("display")),
            )
        )
    return tuple(items)


def _parse_target(entry: dict[str, Any]) -> ConceptMapTargetSpec | None:
    equiv = _opt_str(entry.get("equivalence"))
    if equiv is None:
        return None
    return ConceptMapTargetSpec(
        equivalence=equiv,
        code=_opt_str(entry.get("code")),
        display=_opt_str(entry.get("display")),
        comment=_opt_str(entry.get("comment")),
        depends_on=_parse_depends_on(entry.get("dependsOn")),
        product=_parse_depends_on(entry.get("product")),
    )


def _parse_element(entry: dict[str, Any]) -> ConceptMapElementSpec | None:
    code = _opt_str(entry.get("code"))
    if code is None:
        return None
    raw_targets = entry.get("target")
    targets: list[ConceptMapTargetSpec] = []
    if isinstance(raw_targets, list):
        for raw_target in raw_targets:
            if isinstance(raw_target, dict):
                parsed = _parse_target(raw_target)
                if parsed is not None:
                    targets.append(parsed)
    return ConceptMapElementSpec(
        code=code,
        display=_opt_str(entry.get("display")),
        targets=tuple(targets),
    )


def _parse_unmapped(raw: Any) -> ConceptMapUnmappedSpec | None:
    if not isinstance(raw, dict):
        return None
    mode = _opt_str(raw.get("mode"))
    if mode is None:
        return None
    return ConceptMapUnmappedSpec(
        mode=mode,
        code=_opt_str(raw.get("code")),
        display=_opt_str(raw.get("display")),
        url=_opt_str(raw.get("url")),
    )


def _parse_group(entry: dict[str, Any]) -> ConceptMapGroupSpec:
    raw_elements = entry.get("element")
    elements: list[ConceptMapElementSpec] = []
    if isinstance(raw_elements, list):
        for raw_el in raw_elements:
            if isinstance(raw_el, dict):
                parsed = _parse_element(raw_el)
                if parsed is not None:
                    elements.append(parsed)
    return ConceptMapGroupSpec(
        source=_opt_str(entry.get("source")),
        source_version=_opt_str(entry.get("sourceVersion")),
        target=_opt_str(entry.get("target")),
        target_version=_opt_str(entry.get("targetVersion")),
        elements=tuple(elements),
        unmapped=_parse_unmapped(entry.get("unmapped")),
    )


def parse_concept_map(data: dict[str, Any]) -> ConceptMapSpec | None:
    """Parse a FHIR R4 ConceptMap JSON dict into a ConceptMapSpec."""
    if data.get("resourceType") != "ConceptMap":
        return None
    raw_groups = data.get("group")
    groups: tuple[ConceptMapGroupSpec, ...] = (
        tuple(_parse_group(g) for g in raw_groups if isinstance(g, dict))
        if isinstance(raw_groups, list)
        else ()
    )
    source_uri = _opt_str(data.get("sourceUri")) or _opt_str(data.get("sourceCanonical"))
    target_uri = _opt_str(data.get("targetUri")) or _opt_str(data.get("targetCanonical"))
    return ConceptMapSpec(
        url=_opt_str(data.get("url")) or "",
        version=_opt_str(data.get("version")),
        name=_opt_str(data.get("name")),
        status=_opt_str(data.get("status")),
        source_uri=source_uri,
        target_uri=target_uri,
        groups=groups,
    )


def _group_matches_uris(
    group: ConceptMapGroupSpec,
    spec: ConceptMapSpec,
    clean_src: str | None,
    clean_tgt: str | None,
) -> bool:
    src_ok = (
        clean_src is None
        or _strip_version(group.source) == clean_src
        or _strip_version(spec.source_uri) == clean_src
    )
    tgt_ok = (
        clean_tgt is None
        or _strip_version(group.target) == clean_tgt
        or _strip_version(spec.target_uri) == clean_tgt
    )
    return src_ok and tgt_ok


def _spec_matches_uris(
    spec: ConceptMapSpec,
    source: str | None,
    target: str | None,
) -> bool:
    clean_src = _strip_version(source)
    clean_tgt = _strip_version(target)
    if clean_src is None and clean_tgt is None:
        return True
    spec_src_ok = clean_src is None or _strip_version(spec.source_uri) == clean_src
    spec_tgt_ok = clean_tgt is None or _strip_version(spec.target_uri) == clean_tgt
    if spec_src_ok and spec_tgt_ok:
        return True
    return any(_group_matches_uris(g, spec, clean_src, clean_tgt) for g in spec.groups)


class ConceptMapRegistry:
    """In-memory index of ConceptMapSpec instances by URL and (source, target) URIs."""

    def __init__(self) -> None:
        self._all: list[ConceptMapSpec] = []
        self._by_url: dict[str, list[ConceptMapSpec]] = {}
        self._by_pair: dict[tuple[str | None, str | None], list[ConceptMapSpec]] = {}

    def _add_url_key(self, key: str, spec: ConceptMapSpec) -> None:
        bucket = self._by_url.setdefault(key, [])
        if spec not in bucket:
            bucket.append(spec)

    def _add_pair_key(self, source: str | None, target: str | None, spec: ConceptMapSpec) -> None:
        if source is None and target is None:
            return
        key = (_strip_version(source), _strip_version(target))
        bucket = self._by_pair.setdefault(key, [])
        if spec not in bucket:
            bucket.append(spec)

    def register(self, spec: ConceptMapSpec) -> None:
        """Register a ConceptMapSpec in the registry."""
        if spec not in self._all:
            self._all.append(spec)
        if spec.url:
            self._add_url_key(spec.url, spec)
            clean = spec.url.split("|", 1)[0]
            self._add_url_key(clean, spec)
            if spec.version and "|" not in spec.url:
                self._add_url_key(f"{clean}|{spec.version}", spec)
        self._add_pair_key(spec.source_uri, spec.target_uri, spec)
        for group in spec.groups:
            self._add_pair_key(group.source, group.target, spec)

    def register_dict(self, data: dict[str, Any]) -> ConceptMapSpec | None:
        """Parse and register a ConceptMap dict if valid."""
        spec = parse_concept_map(data)
        if spec is not None:
            self.register(spec)
        return spec

    def find_maps(
        self,
        url: str | None = None,
        source: str | None = None,
        target: str | None = None,
    ) -> list[ConceptMapSpec]:
        """Find registered ConceptMaps matching url and/or source/target URIs."""
        if url is not None:
            candidates = self._by_url.get(url) or self._by_url.get(url.split("|", 1)[0], [])
            return [m for m in candidates if _spec_matches_uris(m, source, target)]

        if source is not None and target is not None:
            pair = (_strip_version(source), _strip_version(target))
            exact = self._by_pair.get(pair)
            if exact:
                return list(exact)

        return [m for m in self._all if _spec_matches_uris(m, source, target)]

    def copy(self) -> ConceptMapRegistry:
        """Return a shallow copy of this registry."""
        cloned = ConceptMapRegistry()
        for spec in self._all:
            cloned.register(spec)
        return cloned


def _depends_on_satisfied(
    target: ConceptMapTargetSpec,
    req_deps: Mapping[str, str] | None,
) -> bool:
    if not target.depends_on:
        return True
    if not req_deps:
        return False
    return all(req_deps.get(dep.property) == dep.value for dep in target.depends_on)


def _group_matches_request(group: ConceptMapGroupSpec, request: TranslateRequest) -> bool:
    src_sys = group.target if request.reverse else group.source
    src_ver = group.target_version if request.reverse else group.source_version
    tgt_sys = group.source if request.reverse else group.target

    if (
        request.system is not None
        and src_sys is not None
        and _strip_version(src_sys) != _strip_version(request.system)
    ):
        return False
    if request.version is not None and src_ver is not None and src_ver != request.version:
        return False
    return not (
        request.target_system is not None
        and tgt_sys is not None
        and _strip_version(tgt_sys) != _strip_version(request.target_system)
    )


def _unmapped_match(
    group: ConceptMapGroupSpec,
    request: TranslateRequest,
    map_url: str,
) -> TranslateMatch | None:
    unmapped = group.unmapped
    if unmapped is None:
        return None
    if unmapped.mode == "provided":
        return TranslateMatch(
            equivalence="equivalent",
            system=group.target,
            code=request.code,
            source=map_url or None,
        )
    if unmapped.mode == "fixed" and unmapped.code:
        return TranslateMatch(
            equivalence="relatedto",
            system=group.target,
            code=unmapped.code,
            display=unmapped.display,
            source=map_url or None,
        )
    return None


def _target_is_positive(
    target: ConceptMapTargetSpec,
    req_deps: Mapping[str, str] | None,
    notes: list[str],
) -> bool:
    if not _depends_on_satisfied(target, req_deps):
        return False
    if target.equivalence in NEGATIVE_EQUIVALENCES or (
        target.equivalence not in POSITIVE_EQUIVALENCES
    ):
        if target.comment:
            notes.append(target.comment)
        return False
    return True


def _evaluate_group_forward(
    group: ConceptMapGroupSpec,
    request: TranslateRequest,
    map_url: str,
    matches: list[TranslateMatch],
    notes: list[str],
) -> None:
    found_element = False
    for element in group.elements:
        if element.code != request.code:
            continue
        found_element = True
        for target in element.targets:
            if not _target_is_positive(target, request.depends_on, notes):
                continue
            matches.append(
                TranslateMatch(
                    equivalence=target.equivalence,
                    system=group.target,
                    code=target.code,
                    display=target.display,
                    comment=target.comment,
                    source=map_url or None,
                    depends_on=target.depends_on,
                    product=target.product,
                )
            )
    if not found_element:
        fallback = _unmapped_match(group, request, map_url)
        if fallback is not None:
            matches.append(fallback)


def _evaluate_group_reverse(
    group: ConceptMapGroupSpec,
    request: TranslateRequest,
    map_url: str,
    matches: list[TranslateMatch],
    notes: list[str],
) -> None:
    for element in group.elements:
        for target in element.targets:
            if target.code != request.code:
                continue
            if not _target_is_positive(target, request.depends_on, notes):
                continue
            matches.append(
                TranslateMatch(
                    equivalence=_REVERSE_EQUIVALENCE.get(target.equivalence, target.equivalence),
                    system=group.source,
                    code=element.code,
                    display=element.display,
                    comment=target.comment,
                    source=map_url or None,
                    depends_on=target.depends_on,
                    product=target.product,
                )
            )


def _evaluate_group(
    group: ConceptMapGroupSpec,
    request: TranslateRequest,
    map_url: str,
    matches: list[TranslateMatch],
    notes: list[str],
) -> None:
    if not _group_matches_request(group, request):
        return
    if request.reverse:
        _evaluate_group_reverse(group, request, map_url, matches, notes)
        return
    _evaluate_group_forward(group, request, map_url, matches, notes)


def _translate_local(
    request: TranslateRequest,
    registry: ConceptMapRegistry,
) -> TranslateResult | None:
    maps = registry.find_maps(url=request.url, source=request.source, target=request.target)
    if not maps:
        return None
    matches: list[TranslateMatch] = []
    notes: list[str] = []
    for spec in maps:
        for group in spec.groups:
            _evaluate_group(group, request, spec.url, matches, notes)
    if matches:
        return TranslateResult(result=True, matches=tuple(matches))
    if notes:
        return TranslateResult(result=False, message=notes[0])
    return None


def _default_translate_db_path() -> Path:
    return Path.home() / ".fhir" / "fhirlance-tx-cache.sqlite"


def _l1_cache_get(key: tuple[str, ...]) -> TranslateResult | None:
    with _TRANSLATE_LOCK:
        return _TRANSLATE_L1_CACHE.get(key)


def _l1_cache_put(key: tuple[str, ...], result: TranslateResult) -> None:
    with _TRANSLATE_LOCK:
        if key not in _TRANSLATE_L1_CACHE and len(_TRANSLATE_L1_CACHE) >= _TRANSLATE_L1_CACHE_MAX:
            _TRANSLATE_L1_CACHE.pop(next(iter(_TRANSLATE_L1_CACHE)))
        _TRANSLATE_L1_CACHE[key] = result


def _init_translate_sqlite(path: Path) -> sqlite3.Connection | None:
    try:
        proc_key = (os.getpid(), path.resolve())
        with _TRANSLATE_LOCK:
            if proc_key in _INITIALIZED_TRANSLATE_DB and path.exists():
                return sqlite3.connect(str(path), timeout=5.0)
            path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(str(path), timeout=5.0)
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tx_translate_cache (
                    cache_key TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            _INITIALIZED_TRANSLATE_DB.add(proc_key)
            return conn
    except (sqlite3.Error, OSError):
        return None


def _serialize_result(res: TranslateResult) -> str:
    return json.dumps(
        {
            "result": res.result,
            "message": res.message,
            "matches": [
                {
                    "equivalence": m.equivalence,
                    "system": m.system,
                    "code": m.code,
                    "display": m.display,
                    "comment": m.comment,
                    "source": m.source,
                }
                for m in res.matches
            ],
        }
    )


def _deserialize_result(raw: str) -> TranslateResult | None:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not isinstance(data.get("result"), bool):
        return None
    matches = tuple(
        TranslateMatch(
            equivalence=item["equivalence"],
            system=_opt_str(item.get("system")),
            code=_opt_str(item.get("code")),
            display=_opt_str(item.get("display")),
            comment=_opt_str(item.get("comment")),
            source=_opt_str(item.get("source")),
        )
        for item in data.get("matches", [])
        if isinstance(item, dict) and isinstance(item.get("equivalence"), str)
    )
    return TranslateResult(
        result=data["result"],
        message=_opt_str(data.get("message")),
        matches=matches,
    )


def _read_translate_sqlite(path: Path, cache_key: str) -> TranslateResult | None:
    conn = _init_translate_sqlite(path)
    if conn is None:
        return None
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT payload FROM tx_translate_cache WHERE cache_key = ? LIMIT 1;",
            (cache_key,),
        )
        row = cur.fetchone()
        if row is not None and isinstance(row[0], str):
            return _deserialize_result(row[0])
    except (sqlite3.Error, OSError):
        return None
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()
    return None


def _write_translate_sqlite(path: Path, cache_key: str, res: TranslateResult) -> None:
    conn = _init_translate_sqlite(path)
    if conn is None:
        return
    try:
        conn.execute(
            "INSERT OR REPLACE INTO tx_translate_cache (cache_key, payload) VALUES (?, ?);",
            (cache_key, _serialize_result(res)),
        )
        conn.commit()
    except (sqlite3.Error, OSError):
        pass
    finally:
        with contextlib.suppress(sqlite3.Error):
            conn.close()


def _parse_match_part(parts: list[Any]) -> TranslateMatch | None:
    equivalence: str | None = None
    system: str | None = None
    code: str | None = None
    display: str | None = None
    source: str | None = None
    comment: str | None = None
    for part in parts:
        if not isinstance(part, dict):
            continue
        name = part.get("name")
        if name == "equivalence":
            equivalence = _opt_str(part.get("valueCode")) or _opt_str(part.get("valueString"))
        elif name == "concept" and isinstance(part.get("valueCoding"), dict):
            coding = part["valueCoding"]
            system = _opt_str(coding.get("system"))
            code = _opt_str(coding.get("code"))
            display = _opt_str(coding.get("display"))
        elif name == "source":
            source = _opt_str(part.get("valueUri")) or _opt_str(part.get("valueString"))
        elif name == "comment":
            comment = _opt_str(part.get("valueString"))
    if equivalence is None or equivalence in NEGATIVE_EQUIVALENCES:
        return None
    return TranslateMatch(
        equivalence=equivalence,
        system=system,
        code=code,
        display=display,
        comment=comment,
        source=source,
    )


def _parse_translate_parameters(data: dict[str, Any]) -> TranslateResult:
    result = False
    message: str | None = None
    matches: list[TranslateMatch] = []
    for param in data.get("parameter", []):
        if not isinstance(param, dict):
            continue
        name = param.get("name")
        if name == "result" and isinstance(param.get("valueBoolean"), bool):
            result = param["valueBoolean"]
        elif name == "message":
            message = _opt_str(param.get("valueString"))
        elif name == "match" and isinstance(param.get("part"), list):
            parsed = _parse_match_part(param["part"])
            if parsed is not None:
                matches.append(parsed)
    return TranslateResult(result=result, message=message, matches=tuple(matches))


def _build_translate_payload(request: TranslateRequest) -> dict[str, Any]:
    params: list[dict[str, Any]] = [{"name": "code", "valueCode": request.code}]
    uri_fields = (
        ("system", request.system),
        ("url", request.url),
        ("source", request.source),
        ("target", request.target),
        ("targetsystem", request.target_system),
    )
    for name, val in uri_fields:
        if val is not None:
            params.append({"name": name, "valueUri": val})
    if request.version is not None:
        params.append({"name": "version", "valueString": request.version})
    if request.reverse:
        params.append({"name": "reverse", "valueBoolean": True})
    if request.depends_on:
        for prop, val in sorted(request.depends_on.items()):
            params.append(
                {
                    "name": "dependency",
                    "part": [
                        {"name": "element", "valueUri": prop},
                        {"name": "concept", "valueCodeableConcept": {"coding": [{"code": val}]}},
                    ],
                }
            )
    return {"resourceType": "Parameters", "parameter": params}


def _execute_remote_translate(
    tx_client: TxClient,
    request: TranslateRequest,
) -> tuple[TranslateResult, bool]:
    server = tx_client.options.server.rstrip("/")
    url = f"{server}/ConceptMap/$translate"
    if not url.startswith(("http://", "https://")):
        return TranslateResult(result=False, message=f"Invalid URL scheme: {url}"), False

    body = json.dumps(_build_translate_payload(request)).encode("utf-8")
    req = urllib.request.Request(  # noqa: S310
        url,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/fhir+json",
            "Accept": "application/fhir+json, application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=tx_client.options.timeout) as resp:  # noqa: S310
            payload = json.loads(resp.read().decode("utf-8"))
            if isinstance(payload, dict):
                return _parse_translate_parameters(payload), True
            return TranslateResult(result=False, message="Unexpected non-dict response"), False
    except urllib.error.HTTPError as exc:
        return (
            TranslateResult(result=False, message=f"Terminology server HTTP {exc.code}"),
            False,
        )
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return TranslateResult(result=False, message=f"Terminology server error: {exc}"), False


def _translate_remote(request: TranslateRequest, tx_client: TxClient) -> TranslateResult:
    if tx_client.options.mode != "remote":
        return TranslateResult(result=False, message="Remote terminology mode is disabled")

    deps_key = json.dumps(sorted(request.depends_on.items())) if request.depends_on else ""
    key_tuple = (
        tx_client.options.server,
        request.code,
        request.system or "",
        request.version or "",
        request.url or "",
        request.source or "",
        request.target or "",
        request.target_system or "",
        str(request.reverse),
        deps_key,
    )
    l1_hit = _l1_cache_get(key_tuple)
    if l1_hit is not None:
        return l1_hit

    cache_path = tx_client.options.cache_path or _default_translate_db_path()
    key_str = json.dumps(key_tuple)
    cached = _read_translate_sqlite(cache_path, key_str)
    if cached is not None:
        _l1_cache_put(key_tuple, cached)
        return cached

    remote_res, cacheable = _execute_remote_translate(tx_client, request)
    if cacheable:
        _l1_cache_put(key_tuple, remote_res)
        _write_translate_sqlite(cache_path, key_str, remote_res)
    return remote_res


def translate_code(
    request: TranslateRequest,
    *,
    registry: ConceptMapRegistry | None = None,
    tx_client: TxClient | None = None,
) -> TranslateResult:
    """Translate a code using local ConceptMapRegistry first, then remote TxClient."""
    if registry is not None:
        local_res = _translate_local(request, registry)
        if local_res is not None:
            return local_res

    if tx_client is not None:
        return _translate_remote(request, tx_client)

    return TranslateResult(result=False, message="No ConceptMap match found")
