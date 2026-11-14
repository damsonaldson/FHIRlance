"""Strict JSON parsing and dataset-level file/directory validation runner."""

from __future__ import annotations

import json
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from itertools import repeat
from pathlib import Path
from typing import Any

from fhirlance.resource_validator import validate_resource

_PERCENT_SCALE = 100.0
_FILE_READ_ERRORS = (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError)


@dataclass(frozen=True, slots=True)
class _ValidationOptions:
    require_canadian_profile: bool = True
    profile_urls: list[str] | None = None


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
    issues = validate_resource(
        resource,
        require_canadian_profile=options.require_canadian_profile,
        profile_urls=options.profile_urls,
    )
    if not issues:
        return True

    res_id = resource.get("id") if isinstance(resource, dict) else None
    entry: dict[str, Any] = {"file": file_name, "id": res_id, "issues": issues}
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
) -> dict[str, Any]:
    """Validate a single file or all FHIR bundles / NDJSON files in a directory."""
    target_path = Path(target)
    if not target_path.exists():
        raise FileNotFoundError(f"Path not found: {target_path}")

    files = _collect_dataset_files(target_path)
    options = _ValidationOptions(
        require_canadian_profile=require_canadian_profile,
        profile_urls=profile_urls,
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
    else:
        for file_path in files:
            total_count, valid_count, issues = _validate_file(file_path, options)
            total_resources += total_count
            valid_resources += valid_count
            all_issues.extend(issues)

    compliance_rate = (
        (valid_resources / total_resources * _PERCENT_SCALE) if total_resources > 0 else 0.0
    )
    return {
        "directory": str(target_path),
        "total_resources": total_resources,
        "valid_resources": valid_resources,
        "invalid_resources": total_resources - valid_resources,
        "compliance_rate": compliance_rate,
        "issues": all_issues,
    }
