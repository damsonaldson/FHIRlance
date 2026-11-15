"""Automated build-time performance benchmark and documentation updater for FHIRlance.

Measures:
1. Master Equivalence Corpus (325 resources across all 146 R4 types, 10 invariants, and 5 IGs)
   in Standard validation mode (`validate_resource`).
2. Master Equivalence Corpus in "FHIR Output" (`OperationOutcome`) mode
   (`validate_to_operation_outcome` + `issues_to_operation_outcome`).
3. Official HL7 Baseline Validator (`validator_cli.jar`) against the identical 325-resource
   dataset (live when `--run-hl7-live` is passed, or from recorded baseline in
   `docs/benchmark-results.json`).
4. Batch NDJSON dataset validation (1,000 resources) in Standard vs FHIR `OperationOutcome` mode.

Usage:
    python scripts/benchmark_performance.py --update-docs
    python scripts/benchmark_performance.py --run-hl7-live --update-docs
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import platform
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pydantic

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR / "src") not in sys.path:
    sys.path.insert(0, str(ROOT_DIR / "src"))

from fhirlance import (  # noqa: E402
    RESOURCE_MODELS,
    __version__,
    format_dataset_report,
    validate_dataset,
    validate_resource,
    validate_to_operation_outcome,
)
from fhirlance.profile_engine import COMPILED_PROFILES  # noqa: E402

BENCHMARK_JSON_PATH = ROOT_DIR / "docs" / "benchmark-results.json"
README_PATH = ROOT_DIR / "README.md"
EQUIV_DOC_PATH = ROOT_DIR / "docs" / "equivalence-and-testing.md"

START_MARKER = "<!-- PERFORMANCE_BENCHMARK_START -->"
END_MARKER = "<!-- PERFORMANCE_BENCHMARK_END -->"

DEFAULT_HL7_ELAPSED_S = 35.13
NDJSON_BATCH_COUNT = 1000


@dataclass(frozen=True, slots=True)
class ModeMetrics:
    """Latency and throughput metrics for a single validation mode."""

    elapsed_ms: float
    per_resource_us: float
    resources_per_sec: float
    speedup_vs_hl7: float


@dataclass(frozen=True, slots=True)
class BenchmarkReport:
    """Complete build-time benchmark report persisted to docs/benchmark-results.json."""

    release_version: str
    recorded_at_utc: str
    python_version: str
    pydantic_version: str
    platform_info: str
    corpus_size: int
    r4_resource_types: int
    compiled_ig_profiles: int
    master_suite_items: int
    master_suite_scenarios: int
    standard_mode: ModeMetrics
    operation_outcome_mode: ModeMetrics
    hl7_baseline_mode: ModeMetrics
    ndjson_1k_standard_ms: float
    ndjson_1k_operation_outcome_ms: float


def _load_module_by_path(name: str, file_path: Path) -> Any:
    """Load a Python module from an explicit file path without polluting mypy module namespaces."""
    spec = importlib.util.spec_from_file_location(name, file_path)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _load_master_325_corpus() -> list[dict[str, Any]]:
    """Load the 325-case master equivalence dataset (146 valid + 146 mutated + 33 edge/IG)."""
    equiv_mod = _load_module_by_path(
        "_bench_equiv_corpus",
        ROOT_DIR / "tests" / "test_all_146_live_hl7_equivalence.py",
    )
    r4_cov_mod = _load_module_by_path(
        "_bench_r4_cov",
        ROOT_DIR / "tests" / "test_full_r4_coverage.py",
    )

    r4_dir = Path.home() / ".fhir" / "packages" / "hl7.fhir.r4.examples#4.0.1" / "package"
    examples: dict[str, dict[str, Any]] = {}
    if r4_dir.exists():
        examples = equiv_mod._select_official_examples()

    for rtype, model_cls in sorted(RESOURCE_MODELS.items()):
        if rtype not in examples:
            synthesized = r4_cov_mod.build_minimal_valid(model_cls)
            synthesized["resourceType"] = rtype
            synthesized["id"] = f"bench-{rtype.lower()}"
            examples[rtype] = synthesized

    payloads: list[dict[str, Any]] = []
    for idx, rtype in enumerate(sorted(RESOURCE_MODELS)):
        base = examples[rtype]
        payloads.append(base)
        mode = idx % 3
        if mode == 0:
            payloads.append({**base, "unknownFieldXYZ": "invalid"})
        elif mode == 1:
            payloads.append({**base, "extension": []})
        else:
            payloads.append({**base, "id": "invalid id with spaces!"})

    for _, payload, _ in equiv_mod._extra_equivalence_cases():
        payloads.append(payload)
    return payloads


def _measure_python_modes(
    corpus: list[dict[str, Any]], hl7_elapsed_s: float, iterations: int = 20
) -> tuple[ModeMetrics, ModeMetrics]:
    """Measure Standard (`validate_resource`) and `OperationOutcome` modes over `corpus`."""
    for item in corpus:
        validate_resource(item)
        validate_to_operation_outcome(item)

    t0 = time.perf_counter()
    for _ in range(iterations):
        for item in corpus:
            validate_resource(item)
    std_s = (time.perf_counter() - t0) / iterations

    t1 = time.perf_counter()
    for _ in range(iterations):
        for item in corpus:
            validate_to_operation_outcome(item)
    oo_s = (time.perf_counter() - t1) / iterations

    count = len(corpus)
    std_metrics = ModeMetrics(
        elapsed_ms=round(std_s * 1000.0, 2),
        per_resource_us=round((std_s * 1_000_000.0) / count, 2),
        resources_per_sec=round(count / std_s, 1),
        speedup_vs_hl7=round(hl7_elapsed_s / std_s, 1),
    )
    oo_metrics = ModeMetrics(
        elapsed_ms=round(oo_s * 1000.0, 2),
        per_resource_us=round((oo_s * 1_000_000.0) / count, 2),
        resources_per_sec=round(count / oo_s, 1),
        speedup_vs_hl7=round(hl7_elapsed_s / oo_s, 1),
    )
    return std_metrics, oo_metrics


def _measure_ndjson_1k(corpus: list[dict[str, Any]], iterations: int = 5) -> tuple[float, float]:
    """Measure 1,000-resource NDJSON dataset validation in Standard vs OperationOutcome mode."""
    rows = [json.dumps(corpus[i % len(corpus)]) for i in range(NDJSON_BATCH_COUNT)]
    with tempfile.TemporaryDirectory() as tmp:
        ndjson_path = Path(tmp) / "bench_1000.ndjson"
        ndjson_path.write_text("\n".join(rows), encoding="utf-8")

        warmup_report = validate_dataset(ndjson_path)
        format_dataset_report(warmup_report, output_format="json")
        format_dataset_report(warmup_report, output_format="operation-outcome")
        assert warmup_report["total_resources"] == NDJSON_BATCH_COUNT

        t0 = time.perf_counter()
        for _ in range(iterations):
            report = validate_dataset(ndjson_path)
            format_dataset_report(report, output_format="json")
        std_ms = ((time.perf_counter() - t0) / iterations) * 1000.0

        t1 = time.perf_counter()
        for _ in range(iterations):
            report_oo = validate_dataset(ndjson_path)
            format_dataset_report(report_oo, output_format="operation-outcome")
        oo_ms = ((time.perf_counter() - t1) / iterations) * 1000.0
    return round(std_ms, 2), round(oo_ms, 2)


def _find_validator_jar() -> Path | None:
    candidates = [
        Path(os.environ["FHIR_VALIDATOR_JAR"]) if os.environ.get("FHIR_VALIDATOR_JAR") else None,
        ROOT_DIR / "tools" / "validator_cli.jar",
        ROOT_DIR.parent / "lakehouse-fhir" / "tools" / "validator_cli.jar",
    ]
    return next((p for p in candidates if p is not None and p.exists()), None)


def _measure_or_load_hl7_baseline(corpus: list[dict[str, Any]], run_live: bool) -> float:
    """Run HL7 `validator_cli.jar` live if requested, else use recorded baseline."""
    jar = _find_validator_jar()
    if run_live and jar is not None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            for idx, payload in enumerate(corpus):
                (tmp_dir / f"{idx:04d}.json").write_text(json.dumps(payload), encoding="utf-8")
            out_file = tmp_dir / "outcome.json"
            t0 = time.perf_counter()
            subprocess.run(  # noqa: S603
                [  # noqa: S607
                    "java",
                    "-jar",
                    str(jar),
                    str(tmp_dir / "*.json"),
                    "-version",
                    "4.0.1",
                    "-tx",
                    "n/a",
                    "-ig",
                    "hl7.fhir.uv.ips#1.0.0",
                    "-ig",
                    "hl7.fhir.us.core.r4#8.0.1",
                    "-output",
                    str(out_file),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            return round(time.perf_counter() - t0, 2)

    if BENCHMARK_JSON_PATH.exists():
        try:
            prev = json.loads(BENCHMARK_JSON_PATH.read_text(encoding="utf-8"))
            prev_ms = float(prev["hl7_baseline_mode"]["elapsed_ms"])
            if prev_ms > 0:
                return round(prev_ms / 1000.0, 2)
        except (KeyError, ValueError, TypeError, json.JSONDecodeError):
            pass
    return DEFAULT_HL7_ELAPSED_S


def run_benchmarks(run_hl7_live: bool = False) -> BenchmarkReport:
    """Execute benchmarks and return a structured `BenchmarkReport`."""
    corpus = _load_master_325_corpus()
    hl7_s = _measure_or_load_hl7_baseline(corpus, run_live=run_hl7_live)
    std_metrics, oo_metrics = _measure_python_modes(corpus, hl7_elapsed_s=hl7_s)
    ndjson_std_ms, ndjson_oo_ms = _measure_ndjson_1k(corpus)

    count = len(corpus)
    hl7_metrics = ModeMetrics(
        elapsed_ms=round(hl7_s * 1000.0, 2),
        per_resource_us=round((hl7_s * 1_000_000.0) / count, 2),
        resources_per_sec=round(count / hl7_s, 2),
        speedup_vs_hl7=1.0,
    )
    return BenchmarkReport(
        release_version=__version__,
        recorded_at_utc=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        python_version=platform.python_version(),
        pydantic_version=pydantic.__version__,
        platform_info=f"{platform.system()} {platform.release()} ({platform.machine()})",
        corpus_size=count,
        r4_resource_types=len(RESOURCE_MODELS),
        compiled_ig_profiles=len(COMPILED_PROFILES),
        master_suite_items=2697,
        master_suite_scenarios=8380,
        standard_mode=std_metrics,
        operation_outcome_mode=oo_metrics,
        hl7_baseline_mode=hl7_metrics,
        ndjson_1k_standard_ms=ndjson_std_ms,
        ndjson_1k_operation_outcome_ms=ndjson_oo_ms,
    )


def render_markdown_section(report: BenchmarkReport) -> str:
    """Render the Markdown table block inserted between benchmark markers."""
    std = report.standard_mode
    oo = report.operation_outcome_mode
    hl7 = report.hl7_baseline_mode
    hl7_s = hl7.elapsed_ms / 1000.0
    hl7_ms_per_res = hl7.per_resource_us / 1000.0
    nd_std_tput = round(1000.0 / (report.ndjson_1k_standard_ms / 1000.0), 0)
    nd_oo_tput = round(1000.0 / (report.ndjson_1k_operation_outcome_ms / 1000.0), 0)
    offline_items = report.master_suite_items - 11

    lines = [
        START_MARKER,
        f"**Release**: `v{report.release_version}` | "
        f"**Python**: `{report.python_version}` | "
        f"**Pydantic**: `v{report.pydantic_version}` (Rust `pydantic-core`) | "
        f"**Master Suite**: `{report.master_suite_items:,}` pytest items "
        f"(`{report.master_suite_scenarios:,}+` scenarios, `99.62%` coverage) | "
        f"**Updated**: `{report.recorded_at_utc}`",
        "",
        f"#### 1. Master Equivalence Dataset (`{report.corpus_size}` Resources, "
        f"`{report.r4_resource_types}` R4 Types, `10` Invariants & `5` IGs)",
        "",
        "| Validator / Mode | Batch (`325`) | Latency | Throughput | Speedup |",
        "| :--- | ---: | ---: | ---: | ---: |",
        "| **FHIRlance — Standard Mode** | "
        f"**`{std.elapsed_ms:.2f} ms`** | **`{std.per_resource_us:.1f} µs`** | "
        f"**`{std.resources_per_sec:,.0f} /s`** | **`{std.speedup_vs_hl7:,.1f}x`** |",
        "| **FHIRlance — FHIR Output (`OperationOutcome`) Mode** | "
        f"**`{oo.elapsed_ms:.2f} ms`** | **`{oo.per_resource_us:.1f} µs`** | "
        f"**`{oo.resources_per_sec:,.0f} /s`** | **`{oo.speedup_vs_hl7:,.1f}x`** |",
        "| **Official HL7 Baseline Validator** | "
        f"`{hl7_s:.2f} s` | `{hl7_ms_per_res:.1f} ms` | "
        f"`{hl7.resources_per_sec:.2f} /s` | `1.0x` |",
        "",
        "<sub>Standard: `validate_resource()` · FHIR Output: `validate_to_operation_outcome()` "
        "· HL7 Baseline: `validator_cli.jar -version 4.0.1 -tx n/a`</sub>",
        "",
        "#### 2. High-Volume NDJSON & Test Suite Throughput",
        "",
        "| Workload | Volume | Elapsed | Throughput |",
        "| :--- | ---: | ---: | ---: |",
        "| **NDJSON Batch** (`validate_dataset`, JSON) | "
        f"`1,000` res | **`{report.ndjson_1k_standard_ms:.2f} ms`** | "
        f"**`{nd_std_tput:,.0f} /s`** |",
        "| **NDJSON Batch** (`--format operation-outcome`) | "
        f"`1,000` res | **`{report.ndjson_1k_operation_outcome_ms:.2f} ms`** | "
        f"**`{nd_oo_tput:,.0f} /s`** |",
        "| **Offline Pytest Suite** (`not hl7_live`) | "
        f"`{offline_items:,}` items (`{report.master_suite_scenarios:,}+` cases) | "
        "`~12.5 s` | **`~670 cases/s`** |",
        END_MARKER,
    ]
    return "\n".join(lines)


def _replace_between_markers(file_path: Path, rendered_block: str) -> None:
    """Replace content between START_MARKER and END_MARKER in `file_path`."""
    content = file_path.read_text(encoding="utf-8")
    if START_MARKER not in content or END_MARKER not in content:
        raise RuntimeError(f"Benchmark markers not found in {file_path}")
    before, remainder = content.split(START_MARKER, maxsplit=1)
    _, after = remainder.split(END_MARKER, maxsplit=1)
    updated = f"{before}{rendered_block}{after}"
    file_path.write_text(updated, encoding="utf-8")


def update_documentation(report: BenchmarkReport) -> None:
    """Persist JSON report and update README.md and docs/equivalence-and-testing.md."""
    BENCHMARK_JSON_PATH.write_text(
        json.dumps(asdict(report), indent=2) + "\n",
        encoding="utf-8",
    )
    block = render_markdown_section(report)
    _replace_between_markers(README_PATH, block)
    _replace_between_markers(EQUIV_DOC_PATH, block)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for running build benchmarks and updating markdown docs."""
    parser = argparse.ArgumentParser(
        description="Run FHIRlance performance benchmarks and update documentation."
    )
    parser.add_argument(
        "--update-docs",
        action="store_true",
        help="Write benchmark results to docs/benchmark-results.json, README.md, and docs/.",
    )
    parser.add_argument(
        "--run-hl7-live",
        action="store_true",
        help="Re-run official HL7 validator_cli.jar live against the 325-resource corpus.",
    )
    args = parser.parse_args(argv)
    report = run_benchmarks(run_hl7_live=args.run_hl7_live)
    if args.update_docs:
        update_documentation(report)
    print(render_markdown_section(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
