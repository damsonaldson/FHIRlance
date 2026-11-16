"""FHIR IG package resolution and safe installation."""

from __future__ import annotations

import json
import os
import re
import shutil
import tarfile
import tempfile
import urllib.error
import urllib.request
from collections import deque
from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Any

_MAX_TAR_MEMBER_BYTES = 25 * 1024 * 1024  # 25 MB
_MAX_DOWNLOAD_BYTES = 128 * 1024 * 1024  # 128 MB
_MAX_TAR_MEMBERS = 5000
_HTTP_TIMEOUT_SECONDS = 30
_SAFE_PKG_PART_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
_REGISTRY_URLS = (
    "https://packages.fhir.org",
    "https://packages.simplifier.net",
)
_SKIPPED_CORE_PACKAGES = frozenset({"hl7.fhir.r4.core", "hl7.fhir.r4.examples"})


def _validate_pkg_part(value: str, label: str) -> str:
    if not value or ".." in value or not _SAFE_PKG_PART_RE.fullmatch(value):
        raise ValueError(f"Invalid package {label}: {value!r}")
    return value


def default_cache_dir() -> Path:
    """Return the FHIRlance cache directory (~/.cache/fhirlance or FHIRLANCE_CACHE_DIR)."""
    env_dir = os.environ.get("FHIRLANCE_CACHE_DIR")
    if env_dir:
        return Path(env_dir).expanduser()
    return Path.home() / ".cache" / "fhirlance"


def _pkg_sort_key(path: Path) -> tuple[Any, ...]:
    name = path.parent.name if path.name == "package" else path.name
    return tuple(int(part) if part.isdigit() else part for part in re.split(r"(\d+)", name))


def _resolve_pkg_subdir(candidate: Path) -> Path:
    pkg_sub = candidate / "package"
    return pkg_sub if pkg_sub.is_dir() else candidate


def find_package_dir(
    pkg_id: str,
    version: str | None = None,
    *,
    cache_dir: Path | None = None,
) -> Path | None:
    """Locate an installed FHIR package directory in FHIRlance or ~/.fhir caches."""
    _validate_pkg_part(pkg_id, "id")
    if version is not None:
        _validate_pkg_part(version, "version")

    base_cache = cache_dir if cache_dir is not None else default_cache_dir()
    search_roots = (
        base_cache / "packages",
        Path.home() / ".fhir" / "packages",
    )

    for root in search_roots:
        if not root.is_dir():
            continue
        if version is not None:
            exact = root / f"{pkg_id}#{version}"
            if exact.exists():
                return _resolve_pkg_subdir(exact)
            continue

        matches = sorted(root.glob(f"{pkg_id}#*"), key=_pkg_sort_key)
        if matches:
            return _resolve_pkg_subdir(matches[-1])
    return None


def _extract_deps_dict(raw_data: Any) -> dict[str, str]:
    if not isinstance(raw_data, dict):
        return {}
    deps = raw_data.get("dependencies")
    if not isinstance(deps, dict):
        return {}
    validated: dict[str, str] = {}
    for k, v in deps.items():
        if isinstance(k, str) and isinstance(v, str) and k and v:
            validated[_validate_pkg_part(k, "id")] = _validate_pkg_part(v, "version")
    return validated


def _read_json_bytes(raw_bytes: bytes) -> dict[str, str]:
    try:
        parsed = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return {}
    return _extract_deps_dict(parsed)


def _read_deps_from_tarball(source: Path) -> dict[str, str]:
    try:
        with tarfile.open(source, "r:gz") as tar:
            for count, member in enumerate(tar, start=1):
                if count > _MAX_TAR_MEMBERS:
                    raise ValueError(f"Tarball exceeds maximum member limit of {_MAX_TAR_MEMBERS}")
                norm = member.name.replace("\\", "/").lstrip("./")
                if norm not in {"package/package.json", "package.json"} or not member.isfile():
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    return {}
                raw_bytes = extracted.read(_MAX_TAR_MEMBER_BYTES + 1)
                if len(raw_bytes) > _MAX_TAR_MEMBER_BYTES:
                    raise ValueError("package.json exceeds maximum member byte limit")
                return _read_json_bytes(raw_bytes)
    except (tarfile.TarError, OSError):
        return {}
    return {}


def read_package_dependencies(source: Path) -> dict[str, str]:
    """Read `dependencies` from package/package.json in a directory or .tgz tarball."""
    if source.is_dir():
        for rel in (Path("package") / "package.json", Path("package.json")):
            candidate = source / rel
            if candidate.is_file():
                try:
                    return _read_json_bytes(candidate.read_bytes())
                except OSError:
                    return {}
        return {}
    if source.is_file():
        return _read_deps_from_tarball(source)
    return {}


def resolve_transitive_packages(
    sources: Sequence[Path],
    *,
    cache_dir: Path | None = None,
) -> list[Path]:
    """Resolve transitive IG package dependencies using BFS with cycle detection."""
    result: list[Path] = []
    visited: set[Path] = set()
    queue: deque[Path] = deque()

    for src in sources:
        resolved = src.resolve()
        if resolved not in visited:
            visited.add(resolved)
            result.append(src)
            queue.append(src)

    while queue:
        current = queue.popleft()
        deps = read_package_dependencies(current)
        for dep_id, dep_version in deps.items():
            if dep_id in _SKIPPED_CORE_PACKAGES:
                continue
            dep_path = find_package_dir(dep_id, dep_version, cache_dir=cache_dir)
            if dep_path is None:
                continue
            dep_resolved = dep_path.resolve()
            if dep_resolved not in visited:
                visited.add(dep_resolved)
                result.append(dep_path)
                queue.append(dep_path)

    return result


def _validate_https_url(url: str) -> None:
    if not url.startswith("https://"):
        raise ValueError(f"Refusing non-HTTPS URL: {url}")


def _download_bytes(url: str) -> bytes:
    _validate_https_url(url)
    req = urllib.request.Request(url, headers={"User-Agent": "fhirlance"})  # noqa: S310
    with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT_SECONDS) as resp:  # noqa: S310
        data: bytes = resp.read(_MAX_DOWNLOAD_BYTES + 1)
    if len(data) > _MAX_DOWNLOAD_BYTES:
        raise ValueError(f"Download exceeds maximum size of {_MAX_DOWNLOAD_BYTES} bytes: {url}")
    return data


def _resolve_latest_version(pkg_id: str) -> str:
    last_exc: Exception | None = None
    for base_url in _REGISTRY_URLS:
        url = f"{base_url}/{pkg_id}"
        try:
            raw = _download_bytes(url)
            meta = json.loads(raw.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            last_exc = exc
            continue
        if isinstance(meta, dict):
            dist_tags = meta.get("dist-tags")
            if isinstance(dist_tags, dict) and isinstance(dist_tags.get("latest"), str):
                return str(dist_tags["latest"])
    raise RuntimeError(f"Unable to resolve latest version for package {pkg_id!r}") from last_exc


def _download_package_tarball(pkg_id: str, version: str) -> bytes:
    last_exc: Exception | None = None
    for base_url in _REGISTRY_URLS:
        url = f"{base_url}/{pkg_id}/{version}"
        try:
            return _download_bytes(url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_exc = exc
    raise RuntimeError(f"Failed to download package {pkg_id}#{version}") from last_exc


def _validate_tar_member(member: tarfile.TarInfo, dest_root: Path) -> Path:
    norm_name = member.name.replace("\\", "/")
    if norm_name.startswith("/") or ":" in norm_name:
        raise ValueError(f"Unsafe tar member path: {member.name!r}")
    parts = PurePosixPath(norm_name).parts
    if ".." in parts:
        raise ValueError(f"Path traversal detected in tar member: {member.name!r}")
    if member.issym() or member.islnk() or not (member.isfile() or member.isdir()):
        raise ValueError(f"Unsupported non-regular tar member: {member.name!r}")

    target_path = (dest_root / PurePosixPath(*parts)).resolve()
    if target_path != dest_root and not target_path.is_relative_to(dest_root):
        raise ValueError(f"Tar member escapes destination directory: {member.name!r}")
    return target_path


def _extract_tarball_safely(tar_path: Path, dest_dir: Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_root = dest_dir.resolve()
    with tarfile.open(tar_path, "r:gz") as tar:
        for count, member in enumerate(tar, start=1):
            if count > _MAX_TAR_MEMBERS:
                raise ValueError(f"Tarball exceeds maximum member limit of {_MAX_TAR_MEMBERS}")
            target_path = _validate_tar_member(member, dest_root)
            if member.isdir():
                target_path.mkdir(parents=True, exist_ok=True)
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            raw_bytes = extracted.read(_MAX_TAR_MEMBER_BYTES + 1)
            if len(raw_bytes) > _MAX_TAR_MEMBER_BYTES:
                raise ValueError(
                    f"Tar member {member.name!r} exceeds {_MAX_TAR_MEMBER_BYTES} byte limit"
                )
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_bytes(raw_bytes)


def _install_single_package(
    pkg_id: str,
    version: str,
    base_cache: Path,
) -> Path:
    _validate_pkg_part(pkg_id, "id")
    _validate_pkg_part(version, "version")
    packages_root = (base_cache / "packages").resolve()
    dest_dir = base_cache / "packages" / f"{pkg_id}#{version}"
    if not dest_dir.resolve().is_relative_to(packages_root):
        raise ValueError(f"Package destination escapes cache directory: {dest_dir}")
    if (dest_dir / "package" / "package.json").is_file():
        return dest_dir / "package"

    tar_bytes = _download_package_tarball(pkg_id, version)
    with tempfile.TemporaryDirectory() as tmp_dir_str:
        tmp_dir = Path(tmp_dir_str)
        tar_path = tmp_dir / "package.tgz"
        tar_path.write_bytes(tar_bytes)
        staging_dir = tmp_dir / "extracted"
        _extract_tarball_safely(tar_path, staging_dir)
        if dest_dir.exists():
            shutil.rmtree(dest_dir)
        dest_dir.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging_dir), str(dest_dir))

    return _resolve_pkg_subdir(dest_dir)


def _parse_pkg_spec(pkg_spec: str) -> tuple[str, str]:
    if not pkg_spec:
        raise ValueError("Package spec must not be empty")
    if "#" in pkg_spec:
        pkg_id, version = pkg_spec.split("#", 1)
        if not pkg_id or not version:
            raise ValueError(f"Invalid package spec: {pkg_spec!r}")
        return _validate_pkg_part(pkg_id, "id"), _validate_pkg_part(version, "version")
    _validate_pkg_part(pkg_spec, "id")
    return pkg_spec, _validate_pkg_part(_resolve_latest_version(pkg_spec), "version")


def install_package(
    pkg_spec: str,
    *,
    cache_dir: Path | None = None,
    include_deps: bool = True,
) -> list[Path]:
    """Download, safely extract, and optionally install dependencies for a FHIR IG package."""
    base_cache = cache_dir if cache_dir is not None else default_cache_dir()
    root_id, root_version = _parse_pkg_spec(pkg_spec)

    installed: list[Path] = []
    visited: set[tuple[str, str]] = set()
    queue: deque[tuple[str, str]] = deque([(root_id, root_version)])

    while queue:
        pkg_id, version = queue.popleft()
        if (pkg_id, version) in visited or pkg_id in _SKIPPED_CORE_PACKAGES:
            continue
        visited.add((pkg_id, version))

        pkg_dir = _install_single_package(pkg_id, version, base_cache)
        installed.append(pkg_dir)

        if not include_deps:
            continue
        for dep_id, dep_version in read_package_dependencies(pkg_dir).items():
            if dep_id not in _SKIPPED_CORE_PACKAGES and (dep_id, dep_version) not in visited:
                queue.append((dep_id, dep_version))

    return installed
