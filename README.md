# FHIRlance

[![CI](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml)
[![CodeQL](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml)

High-performance **FHIR R4 structural & Implementation Guide profile validator** backed by Pydantic v2 (`pydantic-core` in Rust).

## Documentation
- **[CLI, Python API & Architecture Reference](docs/usage-and-architecture.md)** — Full CLI flags, output formats, Python API, module breakdown, and dev workflow.
- **[Proof of Functional Equivalence & Test Suite](docs/equivalence-and-testing.md)** — HL7 `validator_cli.jar` equivalence matrix and test catalog (`2,697` items / `8,380+` scenarios).
- **[Build & CI/CD Architecture](docs/ci-and-build.md)** — Ahead-of-time schema compilation, security gates, and cross-platform CI pipeline.
- **[Architecture & Product Roadmap](docs/roadmap.md)** — Multi-phase roadmap (`v0.1.0`–`v1.0.0`) and HAPI FHIR / Smile CDR integration design.

## Coverage (TL;DR)
- **Full FHIR R4 Base Spec**: All **146 resources** and **39 complex datatypes** (`659` generated Pydantic v2 models, `8,350` fields, `186` `[x]` choice groups, `_primitive` extensions, `ext-1`, core FHIRPath invariants, and recursive `Bundle` / `contained[]` validation).
- **Multi-IG Profile Engine**: **183 pre-compiled profiles** (`2,009` rules) across **HL7 R4 Core, CA-Baseline 1.2.0, Infoway CA Core 1.1.0, HL7 IPS 1.0.0, and HL7 US Core 8.0.1**, plus dynamic runtime `-ig` loading (`.tgz`, folders, Bundles, StructureDefinitions).
- **Canadian Localization**: Opt-in CA-Baseline / PS-CA `meta.profile`, all **13 provincial/territorial JHN systems**, `A1A 1A1` postal code FSA checks, and US-extension restrictions (`--no-canadian` to disable).
- **Standard Output Formats**: Text, JSON, self-validating FHIR R4 `OperationOutcome`, **SARIF v2.1.0**, and **JUnit XML**.

## Performance & Benchmarks

Auto-updated on build via [`scripts/benchmark_performance.py`](scripts/benchmark_performance.py) (raw JSON: [`docs/benchmark-results.json`](docs/benchmark-results.json); full methodology: **[Equivalence & Testing](docs/equivalence-and-testing.md)**).

<!-- PERFORMANCE_BENCHMARK_START -->
**Release**: `v0.1.0` | **Python**: `3.13.18` | **Pydantic**: `v2.14.3` (Rust `pydantic-core`) | **Master Suite**: `2,697` pytest items (`8,380+` scenarios, `99.62%` coverage) | **Updated**: `2026-11-14 19:35 UTC`

#### 1. Master Equivalence Dataset (`325` Resources across all `146` R4 Types, `10` Invariants & `5` IGs)

| Validator / Execution Mode | API / Command | Batch Elapsed (`325` Resources) | Latency per Resource | Throughput (`resources/s`) | Speedup vs. HL7 Baseline |
| :--- | :--- | ---: | ---: | ---: | ---: |
| **FHIRlance — Standard Mode** | `validate_resource(res)` (`list[str]`) | **`13.25 ms`** | **`40.8 µs`** | **`24,532 res/s`** | **`2,651.7x faster`** |
| **FHIRlance — FHIR Output (`OperationOutcome`) Mode** | `validate_to_operation_outcome(res)` (FHIR R4 `OperationOutcome`) | **`15.26 ms`** | **`47.0 µs`** | **`21,292 res/s`** | **`2,301.5x faster`** |
| **Official HL7 Baseline Validator** | `java -jar validator_cli.jar -version 4.0.1 -tx n/a -output` | `35.13 s` (`35,130 ms`) | `108.09 ms` (`108,092 µs`) | `9.25 res/s` | `1.0x` (baseline) |

#### 2. High-Volume NDJSON Dataset & Master Test Suite Throughput

| Benchmark Workload | Mode | Volume | Elapsed Time | Effective Throughput |
| :--- | :--- | ---: | ---: | ---: |
| **NDJSON Dataset Batch (`validate_dataset`)** | Standard Report Mode (`dict` / JSON) | `1,000` resources | **`72.17 ms`** | **`13,856 resources/s`** |
| **NDJSON Dataset Batch (`--format operation-outcome`)** | FHIR R4 `OperationOutcome` Mode | `1,000` resources | **`77.64 ms`** | **`12,880 resources/s`** |
| **Master Offline Pytest Suite (`pytest -m "not hl7_live"`)** | Full R4 (`146` types) + `183` IG Profiles (`2,009` rules) + Fuzzing | `2,686` test items (`8,380+` scenarios) | `~12.5 s` (no-cov) / `~32.9 s` (branch-cov) | **`~670 scenarios/s`** |
<!-- PERFORMANCE_BENCHMARK_END -->

## HL7 Equivalence & Testing (TL;DR)
- **Live `validator_cli.jar` Parity**: Continuously verified against HL7's official Java reference validator (`-version 4.0.1 -tx n/a`) across all 146 R4 resource types, invariants, primitives, and IG profiles with **zero equivalence mismatches**.
- **Exhaustive Test Matrix**: **2,697 pytest items** evaluating **8,380+ validation scenarios** at **99.6% statement and branch coverage**, plus Hypothesis property-based fuzzing.
- **Details**: **[Proof of Functional Equivalence & Test Suite Architecture](docs/equivalence-and-testing.md)**.

## Quick Start (TL;DR)

```bash
# Install (with dev tools)
pip install -e ".[dev]"

# Validate a file or directory (parallel, base R4 + IG profiles, OperationOutcome output)
fhirlance path/to/data --no-canadian --parallel --operation-outcome -o outcome.json

# Validate with custom runtime IGs (.tgz, folder, or cached package) and explicit profiles
fhirlance path/to/data --no-canadian -ig path/to/custom-ig.tgz --profile http://hl7.org/fhir/StructureDefinition/vitalsigns
```

```python
from fhirlance import validate_dataset, validate_resource, validate_to_operation_outcome

issues = validate_resource(resource_dict, require_canadian_profile=False)
outcome = validate_to_operation_outcome(resource_dict, require_canadian_profile=False)
report = validate_dataset("path/to/data", parallel=True, require_canadian_profile=False)
```

- **Full CLI flags, exit codes, Python API & module guide**: **[CLI, Python API & Architecture Reference](docs/usage-and-architecture.md)**.

## Architecture & CI/CD (TL;DR)
- **Ahead-of-Time Codegen + Rust Hot Path**: `scripts/generate_models.py` compiles HL7 FHIR packages into `types.py`, `resources.py`, and `profiles.py` with zero runtime schema I/O and no Python `@model_validator(mode="before")` on `FHIRBaseModel`.
- **Quality & Security Gates**: Enforces `ruff`, strict `mypy` (`pydantic.mypy`), `pytest --cov-fail-under=95` across Linux/Windows (Python 3.10–3.13), `pip-audit`, CodeQL, and clean-room wheel smoke tests.
- **Details**: **[Build & CI/CD Architecture](docs/ci-and-build.md)** and **[CLI, Python API & Architecture Reference](docs/usage-and-architecture.md)**.

## Roadmap & HAPI FHIR / Smile CDR Integration (TL;DR)
- **Phase 1 (`v0.1.0` — Done)**: In-process Python API & batch CLI with `validator_cli.jar` parity (`~36–39 µs/res`).
- **Phase 2 (`v0.2.0` — Next)**: `fhirlance serve` persistent `$validate` daemon over Unix Domain Sockets & HTTP (`~150–250 µs/res`).
- **Phase 3 (`v0.3.0`)**: HAPI FHIR / Smile CDR raw-byte interceptor & Envoy edge filter (`< 0.3 ms`, bypassing JVM POJO/DOM parsing).
- **Phase 4 (`v0.4.0`)**: Embedded MMAP/SQLite terminology accelerator (`-tx` offline), extended FHIRPath compiler, and FHIR R4B/R5 codegen.
- **Phase 5 (`v1.0.0`)**: Standalone Rust C-ABI library (`libfhirlance`) + Java 21+ Project Panama FFI (`~20–35 µs` in-process JVM).
- **Details**: **[Architecture & Product Roadmap](docs/roadmap.md)**.

## License
Copyright (c) 2026 **Brightwood Consulting Group Limited**. Licensed under **[CC BY-NC 4.0](LICENSE)** (free for non-commercial use with attribution).
