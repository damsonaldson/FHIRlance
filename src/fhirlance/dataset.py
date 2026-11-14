"""Strict JSON parsing and dataset-level file/directory validation runner."""

from __future__ import annotations

import json
import os
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field
from itertools import repeat
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fhirlance.ig_loader import load_compiled_ig_profiles
from fhirlance.resource_validator import validate_resource
from fhirlance.terminology import TxOptions, parse_tx_options

if TYPE_CHECKING:
    from collections.abc import Sequence

    from fhirlance.profile_engine import CompiledProfile

_PERCENT_SCALE = 100.0
_FILE_READ_ERRORS = (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError)


@dataclass(frozen=True, slots=True)
class _ValidationOptions:
    require_canadian_profile: bool = True
    profile_urls: tuple[str, ...] | None = None
    ig_sources: tuple[str, ...] | None = None
    compiled_profiles: dict[str, CompiledProfile] | None = None
    tx_options: TxOptions = field(default_factory=TxOptions)


def _reject_bad_json_constant(val: str) -> Any:
    raise ValueError(f"Invalid non-standard JSON numeric constant: {val}")


def loads_strict_json(raw: str) -> Any:
    """Parse JSON strictly, rejecting NaN, Infinity, and -Infinity."""
    return json.loads(raw, parse_constant=_reject_bad_json_constant)


def _record_validation(
    resource: Any,
    file_name: str,
    issues_list: list[dict[str, Any]],
    options: _ValidationOptions,
    *,
    line_no: int | None = None,
) -> bool:
    """Validate one resource and append any issues; return True if valid."""
    effective_ig = (
        options.compiled_profiles if options.compiled_profiles is not None else options.ig_sources
    )
    warnings: list[str] = []
    issues = validate_resource(
        resource,
        require_canadian_profile=options.require_canadian_profile,
        profile_urls=list(options.profile_urls) if options.profile_urls else None,
        ig_sources=effective_ig,
        tx=options.tx_options,
        _warnings_out=warnings,
    )
    res_id = resource.get("id") if isinstance(resource, dict) else None
    res_type = resource.get("resourceType") if isinstance(resource, dict) else None

    if warnings and not issues:
        warn_entry: dict[str, Any] = {
            "file": file_name,
            "resourceType": res_type,
            "id": res_id,
            "warnings": warnings,
        }
        if line_no is not None:
            warn_entry["line"] = line_no
        issues_list.append(warn_entry)
        return True

    if not issues:
        return True

    entry: dict[str, Any] = {
        "file": file_name,
        "resourceType": res_type,
        "id": res_id,
        "issues": issues,
    }
    if warnings:
        entry["warnings"] = warnings
    if line_no is not None:
        entry["line"] = line_no
    issues_list.append(entry)
    return False


def _iter_json_resources(data: Any) -> list[Any]:
    if isinstance(data, dict) and data.get("resourceType") == "Bundle":
        return [
            entry["resource"]
            for entry in (data.get("entry") or [])
            if isinstance(entry, dict) and entry.get("resource") is not None
        ]
    return [data]


def _validate_resource_batch(
    args: tuple[list[Any], str, _ValidationOptions],
) -> tuple[int, int, list[dict[str, Any]]]:
    """Picklable worker for validating a batch of in-memory resources from a Bundle."""
    batch, file_name, options = args
    issues_list: list[dict[str, Any]] = []
    valid = sum(int(_record_validation(res, file_name, issues_list, options)) for res in batch)
    return len(batch), valid, issues_list


def _validate_ndjson_chunk(
    args: tuple[list[tuple[int, str]], str, _ValidationOptions],
) -> tuple[int, int, list[dict[str, Any]]]:
    """Picklable worker for validating a chunk of (line_no, line_str) tuples from an NDJSON file."""
    chunk, file_name, options = args
    total = len(chunk)
    valid = 0
    issues_list: list[dict[str, Any]] = []
    for line_no, line_str in chunk:
        try:
            resource = loads_strict_json(line_str)
        except (json.JSONDecodeError, ValueError) as exc:
            issues_list.append({"file": file_name, "line": line_no, "error": str(exc)})
            continue
        valid += int(
            _record_validation(
                resource,
                file_name,
                issues_list,
                options,
                line_no=line_no,
            )
        )
    return total, valid, issues_list


def _validate_json_file(
    path: Path,
    options: _ValidationOptions,
) -> tuple[int, int, list[dict[str, Any]]]:
    issues_list: list[dict[str, Any]] = []
    try:
        data = loads_strict_json(path.read_text(encoding="utf-8"))
    except _FILE_READ_ERRORS as exc:
        issues_list.append({"file": path.name, "error": str(exc)})
        return 0, 0, issues_list

    resources = _iter_json_resources(data)
    valid = sum(int(_record_validation(res, path.name, issues_list, options)) for res in resources)
    return len(resources), valid, issues_list


def _validate_ndjson_file(
    path: Path,
    options: _ValidationOptions,
) -> tuple[int, int, list[dict[str, Any]]]:
    total = 0
    valid = 0
    issues_list: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                line_str = line.strip()
                if not line_str:
                    continue
                total += 1
                try:
                    resource = loads_strict_json(line_str)
                except (json.JSONDecodeError, ValueError) as exc:
                    issues_list.append({"file": path.name, "line": line_no, "error": str(exc)})
                    continue
                valid += int(
                    _record_validation(
                        resource,
                        path.name,
                        issues_list,
                        options,
                        line_no=line_no,
                    )
                )
    except (OSError, UnicodeDecodeError) as exc:
        issues_list.append({"file": path.name, "error": str(exc)})
    return total, valid, issues_list


def _validate_file(
    path_str: str,
    options: _ValidationOptions,
) -> tuple[int, int, list[dict[str, Any]]]:
    """Worker function to validate a single JSON or NDJSON file."""
    path = Path(path_str)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _validate_json_file(path, options)
    if suffix == ".ndjson":
        return _validate_ndjson_file(path, options)
    return 0, 0, []


def _validate_json_file_parallel(
    path: Path,
    options: _ValidationOptions,
) -> tuple[int, int, list[dict[str, Any]]]:
    issues_list: list[dict[str, Any]] = []
    try:
        data = loads_strict_json(path.read_text(encoding="utf-8"))
    except _FILE_READ_ERRORS as exc:
        issues_list.append({"file": path.name, "error": str(exc)})
        return 0, 0, issues_list

    resources = _iter_json_resources(data)
    if len(resources) <= 1:
        valid = sum(
            int(_record_validation(res, path.name, issues_list, options)) for res in resources
        )
        return len(resources), valid, issues_list

    workers = min(8, os.cpu_count() or 4)
    chunk_size = max(1, (len(resources) + workers - 1) // workers)
    chunks = [
        (resources[i : i + chunk_size], path.name, options)
        for i in range(0, len(resources), chunk_size)
    ]
    total_count = 0
    valid_count = 0
    all_issues: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for t, v, issues in pool.map(_validate_resource_batch, chunks):
            total_count += t
            valid_count += v
            all_issues.extend(issues)
    return total_count, valid_count, all_issues


def _validate_ndjson_file_parallel(
    path: Path,
    options: _ValidationOptions,
) -> tuple[int, int, list[dict[str, Any]]]:
    issues_list: list[dict[str, Any]] = []
    items: list[tuple[int, str]] = []
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_no, line in enumerate(handle, 1):
                line_str = line.strip()
                if line_str:
                    items.append((line_no, line_str))
    except (OSError, UnicodeDecodeError) as exc:
        issues_list.append({"file": path.name, "error": str(exc)})
        return 0, 0, issues_list

    if len(items) <= 1:
        total = len(items)
        valid = 0
        for line_no, line_str in items:
            try:
                resource = loads_strict_json(line_str)
            except (json.JSONDecodeError, ValueError) as exc:
                issues_list.append({"file": path.name, "line": line_no, "error": str(exc)})
                continue
            valid += int(
                _record_validation(
                    resource,
                    path.name,
                    issues_list,
                    options,
                    line_no=line_no,
                )
            )
        return total, valid, issues_list

    workers = min(8, os.cpu_count() or 4)
    chunk_size = max(1, (len(items) + workers - 1) // workers)
    chunks_ndjson = [
        (items[i : i + chunk_size], path.name, options) for i in range(0, len(items), chunk_size)
    ]
    total_count = 0
    valid_count = 0
    all_issues: list[dict[str, Any]] = []
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for t, v, issues in pool.map(_validate_ndjson_chunk, chunks_ndjson):
            total_count += t
            valid_count += v
            all_issues.extend(issues)
    return total_count, valid_count, all_issues


def _validate_file_parallel(
    path_str: str,
    options: _ValidationOptions,
) -> tuple[int, int, list[dict[str, Any]]]:
    """Validate a single file using intra-file chunked parallelism if it has multiple items."""
    path = Path(path_str)
    suffix = path.suffix.lower()
    if suffix == ".json":
        return _validate_json_file_parallel(path, options)
    if suffix == ".ndjson":
        return _validate_ndjson_file_parallel(path, options)
    return 0, 0, []


def _collect_dataset_files(target_path: Path) -> list[str]:
    if target_path.is_file():
        return [str(target_path)]
    discovered = sorted(list(target_path.glob("**/*.json")) + list(target_path.glob("**/*.ndjson")))
    return [str(p) for p in discovered]


def validate_dataset(
    target: Path | str,
    parallel: bool = False,
    require_canadian_profile: bool = True,
    profile_urls: list[str] | None = None,
    ig_sources: Sequence[str | Path] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Validate a single file or all FHIR bundles / NDJSON files in a directory."""
    target_path = Path(target)
    if not target_path.exists():
        raise FileNotFoundError(f"Path not found: {target_path}")

    compiled_map = load_compiled_ig_profiles(ig_sources) if ig_sources else None

    tx_raw = kwargs.get("tx", "local")
    strict_extensible = bool(kwargs.get("strict_extensible", False))
    tx_options = (
        tx_raw
        if isinstance(tx_raw, TxOptions)
        else parse_tx_options(tx_raw, strict_extensible=strict_extensible)
    )

    files = _collect_dataset_files(target_path)
    options = _ValidationOptions(
        require_canadian_profile=require_canadian_profile,
        profile_urls=tuple(profile_urls) if profile_urls else None,
        ig_sources=tuple(str(s) for s in ig_sources) if ig_sources else None,
        compiled_profiles=compiled_map,
        tx_options=tx_options,
    )
    total_resources = 0
    valid_resources = 0
    all_issues: list[dict[str, Any]] = []

    if parallel and len(files) > 1:
        with ProcessPoolExecutor() as pool:
            for total_count, valid_count, issues in pool.map(
                _validate_file, files, repeat(options)
            ):
                total_resources += total_count
                valid_resources += valid_count
                all_issues.extend(issues)
    elif parallel and len(files) == 1:
        total_resources, valid_resources, all_issues = _validate_file_parallel(files[0], options)
    else:
        for file_path in files:
            total_count, valid_count, issues = _validate_file(file_path, options)
            total_resources += total_count
            valid_resources += valid_count
            all_issues.extend(issues)

    compliance_rate = (
        (valid_resources / total_resources * _PERCENT_SCALE) if total_resources > 0 else 0.0
    )
    issues_only = [item for item in all_issues if "error" in item or item.get("issues")]
    warnings_only = [item for item in all_issues if item.get("warnings")]
    return {
        "directory": str(target_path),
        "total_resources": total_resources,
        "valid_resources": valid_resources,
        "invalid_resources": total_resources - valid_resources,
        "compliance_rate": compliance_rate,
        "issues": issues_only,
        "warnings": warnings_only,
    }
