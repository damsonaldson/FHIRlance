"""Unit tests for fhirlance.pkg_manager and CLI package/unknown-profile options."""

from __future__ import annotations

import io
import json
import tarfile
import urllib.error
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from fhirlance import cli, pkg_manager


def _make_tgz_bytes(files: dict[str, bytes], *, symlinks: dict[str, str] | None = None) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
        if symlinks:
            for name, target in symlinks.items():
                info = tarfile.TarInfo(name=name)
                info.type = tarfile.SYMTYPE
                info.linkname = target
                tar.addfile(info)
    return buf.getvalue()


def _write_pkg_dir(root: Path, pkg_id: str, version: str, deps: dict[str, str]) -> Path:
    pkg_dir = root / f"{pkg_id}#{version}" / "package"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    (pkg_dir / "package.json").write_text(
        json.dumps({"name": pkg_id, "version": version, "dependencies": deps}),
        encoding="utf-8",
    )
    return pkg_dir


def test_default_cache_dir_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FHIRLANCE_CACHE_DIR", str(tmp_path / "custom-cache"))
    assert pkg_manager.default_cache_dir() == (tmp_path / "custom-cache")

    monkeypatch.delenv("FHIRLANCE_CACHE_DIR", raising=False)
    assert pkg_manager.default_cache_dir() == Path.home() / ".cache" / "fhirlance"


def test_find_package_dir_versions_and_fallback(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    cache_dir = tmp_path / "cache"
    pkgs_root = cache_dir / "packages"
    _write_pkg_dir(pkgs_root, "example.ig", "1.2.0", {})
    latest = _write_pkg_dir(pkgs_root, "example.ig", "1.10.0", {})

    assert pkg_manager.find_package_dir("example.ig", "1.2.0", cache_dir=cache_dir) == (
        pkgs_root / "example.ig#1.2.0" / "package"
    )
    assert pkg_manager.find_package_dir("example.ig", cache_dir=cache_dir) == latest
    assert pkg_manager.find_package_dir("missing.ig", cache_dir=cache_dir) is None
    assert pkg_manager.find_package_dir("missing.ig", "1.0.0", cache_dir=cache_dir) is None

    fake_home = tmp_path / "home"
    fhir_pkgs = fake_home / ".fhir" / "packages"
    fallback_dir = _write_pkg_dir(fhir_pkgs, "legacy.ig", "2.0.0", {})
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: fake_home))
    assert pkg_manager.find_package_dir("legacy.ig", "2.0.0", cache_dir=cache_dir) == fallback_dir


def test_read_package_dependencies_dir_and_tgz(tmp_path: Path) -> None:
    pkg_dir = _write_pkg_dir(tmp_path, "a.ig", "1.0.0", {"b.ig": "2.0.0"})
    assert pkg_manager.read_package_dependencies(pkg_dir.parent) == {"b.ig": "2.0.0"}
    assert pkg_manager.read_package_dependencies(pkg_dir) == {"b.ig": "2.0.0"}

    tgz_path = tmp_path / "a.ig.tgz"
    tgz_path.write_bytes(
        _make_tgz_bytes(
            {
                "package/package.json": json.dumps(
                    {"name": "a.ig", "dependencies": {"c.ig": "3.0.0"}}
                ).encode("utf-8")
            }
        )
    )
    assert pkg_manager.read_package_dependencies(tgz_path) == {"c.ig": "3.0.0"}
    assert pkg_manager.read_package_dependencies(tmp_path / "does-not-exist") == {}

    bad_tgz = tmp_path / "bad.tgz"
    bad_tgz.write_bytes(b"not a tar")
    assert pkg_manager.read_package_dependencies(bad_tgz) == {}


def test_resolve_transitive_packages_cycles_and_core_skip(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    pkgs_root = cache_dir / "packages"

    pkg_a = _write_pkg_dir(
        pkgs_root,
        "a.ig",
        "1.0.0",
        {
            "b.ig": "1.0.0",
            "hl7.fhir.r4.core": "4.0.1",
            "hl7.fhir.r4.examples": "4.0.1",
        },
    )
    pkg_b = _write_pkg_dir(
        pkgs_root,
        "b.ig",
        "1.0.0",
        {"a.ig": "1.0.0", "c.ig": "1.0.0", "missing.ig": "0.1.0"},
    )
    pkg_c = _write_pkg_dir(pkgs_root, "c.ig", "1.0.0", {})
    _write_pkg_dir(pkgs_root, "hl7.fhir.r4.core", "4.0.1", {})

    resolved = pkg_manager.resolve_transitive_packages([pkg_a], cache_dir=cache_dir)
    assert resolved == [pkg_a, pkg_b, pkg_c]


def test_install_package_with_deps_and_fallback(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    root_tgz = _make_tgz_bytes(
        {
            "package/package.json": json.dumps(
                {
                    "name": "root.ig",
                    "version": "1.0.0",
                    "dependencies": {
                        "dep.ig": "2.0.0",
                        "hl7.fhir.r4.core": "4.0.1",
                    },
                }
            ).encode("utf-8"),
            "package/StructureDefinition-Root.json": b'{"resourceType":"StructureDefinition"}',
        }
    )
    dep_tgz = _make_tgz_bytes(
        {
            "package/package.json": json.dumps({"name": "dep.ig", "version": "2.0.0"}).encode(
                "utf-8"
            ),
        }
    )

    calls: list[str] = []

    def fake_download(url: str) -> bytes:
        calls.append(url)
        if url == "https://packages.fhir.org/root.ig":
            return json.dumps({"dist-tags": {"latest": "1.0.0"}}).encode("utf-8")
        if url == "https://packages.fhir.org/root.ig/1.0.0":
            raise urllib.error.URLError("primary down")
        if url == "https://packages.simplifier.net/root.ig/1.0.0":
            return root_tgz
        if url == "https://packages.fhir.org/dep.ig/2.0.0":
            return dep_tgz
        raise AssertionError(f"Unexpected URL: {url}")

    with patch("fhirlance.pkg_manager._download_bytes", side_effect=fake_download):
        installed = pkg_manager.install_package("root.ig", cache_dir=cache_dir)

    assert installed == [
        cache_dir / "packages" / "root.ig#1.0.0" / "package",
        cache_dir / "packages" / "dep.ig#2.0.0" / "package",
    ]
    assert (installed[0] / "StructureDefinition-Root.json").is_file()
    assert "https://packages.simplifier.net/root.ig/1.0.0" in calls

    # Second call uses cached package without hitting HTTP
    with patch("fhirlance.pkg_manager._download_bytes", side_effect=AssertionError("no network")):
        cached = pkg_manager.install_package("root.ig#1.0.0", cache_dir=cache_dir)
    assert cached == installed

    # Calling with core package directly skips it cleanly
    assert pkg_manager.install_package("hl7.fhir.r4.core#4.0.1", cache_dir=cache_dir) == []


@pytest.mark.parametrize(
    ("files", "symlinks", "expected_msg"),
    [
        ({"../evil.txt": b"x"}, None, "Path traversal"),
        ({"/etc/passwd": b"x"}, None, "Unsafe tar member"),
        ({"package/link": b""}, {"package/sym": "/etc/passwd"}, "non-regular"),
    ],
)
def test_install_package_rejects_unsafe_tar(
    tmp_path: Path,
    files: dict[str, bytes],
    symlinks: dict[str, str] | None,
    expected_msg: str,
) -> None:
    bad_tgz = _make_tgz_bytes(files, symlinks=symlinks)
    with (
        patch("fhirlance.pkg_manager._download_bytes", return_value=bad_tgz),
        pytest.raises(ValueError, match=expected_msg),
    ):
        pkg_manager.install_package("bad.ig#1.0.0", cache_dir=tmp_path / "cache")


def test_install_package_rejects_oversized_tar_member(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(pkg_manager, "_MAX_TAR_MEMBER_BYTES", 5)
    big_tgz = _make_tgz_bytes({"package/big.json": b"123456"})
    with (
        patch("fhirlance.pkg_manager._download_bytes", return_value=big_tgz),
        pytest.raises(ValueError, match="byte limit"),
    ):
        pkg_manager.install_package("big.ig#1.0.0", cache_dir=tmp_path / "cache")


def test_ig_disk_cache_roundtrip_and_corruption(tmp_path: Path) -> None:
    cache_dir = tmp_path / "cache"
    assert pkg_manager.load_ig_disk_cache("missing-key", cache_dir=cache_dir) is None

    payload: dict[str, Any] = {"profiles": {"http://example.org/p": {"required": ["id"]}}}
    pkg_manager.save_ig_disk_cache("ig-key-1", payload, cache_dir=cache_dir)
    assert pkg_manager.load_ig_disk_cache("ig-key-1", cache_dir=cache_dir) == payload

    cache_file = next((cache_dir / "ig").glob("*.json"))
    cache_file.write_text("{broken json", encoding="utf-8")
    assert pkg_manager.load_ig_disk_cache("ig-key-1", cache_dir=cache_dir) is None

    cache_file.write_text("[1, 2, 3]", encoding="utf-8")
    assert pkg_manager.load_ig_disk_cache("ig-key-1", cache_dir=cache_dir) is None


def test_cli_pkg_install_and_unknown_profile(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    cache_dir = tmp_path / "cache"
    pkg_dir = cache_dir / "packages" / "example.ig#1.0.0" / "package"

    with patch.object(cli, "install_package", return_value=[pkg_dir]) as mock_install:
        rc = cli.main(["pkg", "install", "example.ig#1.0.0", "--cache-dir", str(cache_dir)])
    assert rc == 0
    mock_install.assert_called_once_with("example.ig#1.0.0", cache_dir=cache_dir, include_deps=True)
    assert str(pkg_dir) in capsys.readouterr().out

    with patch.object(cli, "install_package", side_effect=ValueError("bad spec")):
        err_rc = cli.main(["pkg", "install", "bad"])
    assert err_rc == 1
    assert "bad spec" in capsys.readouterr().err

    target = tmp_path / "patient.json"
    target.write_text('{"resourceType": "Patient"}', encoding="utf-8")
    fake_report: dict[str, Any] = {
        "total_resources": 1,
        "valid_resources": 1,
        "invalid_resources": 0,
        "compliance_rate": 100.0,
        "issues": [],
    }
    with patch.object(cli, "validate_dataset", return_value=fake_report) as mock_val:
        val_rc = cli.main([str(target), "--unknown-profile", "error"])
    assert val_rc == 0
    assert mock_val.call_args.kwargs["unknown_profile"] == "error"

    with patch.object(cli, "validate_dataset", return_value=fake_report) as mock_val_default:
        default_rc = cli.main([str(target)])
    assert default_rc == 0
    assert mock_val_default.call_args.kwargs["unknown_profile"] == "ignore"


def test_download_bytes_and_registry_failures(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="non-HTTPS"):
        pkg_manager._download_bytes("http://example.com/pkg.tgz")

    class _FakeResp:
        def __init__(self, payload: bytes) -> None:
            self._payload = payload

        def __enter__(self) -> _FakeResp:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return self._payload

    with patch("urllib.request.urlopen", return_value=_FakeResp(b"ok")):
        assert pkg_manager._download_bytes("https://packages.fhir.org/x") == b"ok"

    with (
        patch("fhirlance.pkg_manager._download_bytes", side_effect=urllib.error.URLError("down")),
        pytest.raises(RuntimeError, match="Unable to resolve latest version"),
    ):
        pkg_manager.install_package("missing.ig", cache_dir=tmp_path / "cache")

    with (
        patch("fhirlance.pkg_manager._download_bytes", side_effect=urllib.error.URLError("down")),
        pytest.raises(RuntimeError, match="Failed to download package"),
    ):
        pkg_manager.install_package("missing.ig#1.0.0", cache_dir=tmp_path / "cache")


def test_install_package_edge_cases(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cache_dir = tmp_path / "cache"
    for bad_spec in ("", "foo#", "#1.0.0"):
        with pytest.raises(ValueError, match="spec"):
            pkg_manager.install_package(bad_spec, cache_dir=cache_dir)

    # Tarball with directory entry + include_deps=False
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        dir_info = tarfile.TarInfo(name="package")
        dir_info.type = tarfile.DIRTYPE
        tar.addfile(dir_info)
        pkg_json = json.dumps({"name": "solo.ig", "dependencies": {"dep.ig": "1.0.0"}}).encode(
            "utf-8"
        )
        file_info = tarfile.TarInfo(name="package/package.json")
        file_info.size = len(pkg_json)
        tar.addfile(file_info, io.BytesIO(pkg_json))

    with patch("fhirlance.pkg_manager._download_bytes", return_value=buf.getvalue()):
        installed = pkg_manager.install_package(
            "solo.ig#1.0.0", cache_dir=cache_dir, include_deps=False
        )
    assert installed == [cache_dir / "packages" / "solo.ig#1.0.0" / "package"]

    # _MAX_TAR_MEMBERS exceeded
    monkeypatch.setattr(pkg_manager, "_MAX_TAR_MEMBERS", 1)
    with (
        patch("fhirlance.pkg_manager._download_bytes", return_value=buf.getvalue()),
        pytest.raises(ValueError, match="maximum member limit"),
    ):
        pkg_manager.install_package("many.ig#1.0.0", cache_dir=cache_dir)


def test_read_package_dependencies_edge_cases(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert pkg_manager.read_package_dependencies(empty_dir) == {}

    bad_json_dir = tmp_path / "bad_json"
    bad_json_dir.mkdir()
    (bad_json_dir / "package.json").write_text("[1, 2, 3]", encoding="utf-8")
    assert pkg_manager.read_package_dependencies(bad_json_dir) == {}

    (bad_json_dir / "package.json").write_text("{bad", encoding="utf-8")
    assert pkg_manager.read_package_dependencies(bad_json_dir) == {}

    no_pkg_json_tgz = tmp_path / "no_pkg.tgz"
    no_pkg_json_tgz.write_bytes(_make_tgz_bytes({"package/other.json": b"{}"}))
    assert pkg_manager.read_package_dependencies(no_pkg_json_tgz) == {}

    two_file_tgz = tmp_path / "two.tgz"
    two_file_tgz.write_bytes(_make_tgz_bytes({"a.txt": b"1", "package/package.json": b"{}"}))
    with patch.object(pkg_manager, "_MAX_TAR_MEMBERS", 1), pytest.raises(ValueError, match="limit"):
        pkg_manager.read_package_dependencies(two_file_tgz)

    big_pkg_json_tgz = tmp_path / "big_pkg_json.tgz"
    big_pkg_json_tgz.write_bytes(_make_tgz_bytes({"package/package.json": b'{"dependencies":{}}'}))
    with (
        patch.object(pkg_manager, "_MAX_TAR_MEMBER_BYTES", 5),
        pytest.raises(ValueError, match="byte limit"),
    ):
        pkg_manager.read_package_dependencies(big_pkg_json_tgz)
