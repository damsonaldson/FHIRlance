# FHIRlance

[![CI](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml)
[![CodeQL](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml)

High-performance **FHIR R4 structural & Implementation Guide profile validator** backed by Pydantic v2 (`pydantic-core` in Rust).

## Documentation
- **[CLI, Python API & Architecture Reference](docs/usage-and-architecture.md)** — Full CLI flags, output formats, Python API, module breakdown, and dev workflow.
- **[Terminology Validation Engine & TX Reference](docs/terminology.md)** — Offline grammars (UCUM, BCP-47, MIME, ISO-3166), 1,059 complete CodeSystems, 1,442 ValueSets, `--tx` modes, and L1/SQLite caching.
- **[Proof of Functional Equivalence & Test Suite](docs/equivalence-and-testing.md)** — HL7 `validator_cli.jar` equivalence matrix and test catalog (`2,697` items / `8,380+` scenarios).
- **[Build & CI/CD Architecture](docs/ci-and-build.md)** — Ahead-of-time schema compilation, security gates, and cross-platform CI pipeline.
- **[Architecture & Product Roadmap](docs/roadmap.md)** — Multi-phase roadmap (`v0.1.0`–`v1.0.0`) and HAPI FHIR / Smile CDR integration design.

## Coverage (TL;DR)
- **Full FHIR R4 Base Spec**: All **146 resources** and **39 complex datatypes** (`659` generated Pydantic v2 models, `8,350` fields, `186` `[x]` choice groups, `_primitive` extensions, `ext-1`, core FHIRPath invariants, and recursive `Bundle` / `contained[]` validation).
- **Multi-IG Profile Engine**: **183 pre-compiled profiles** (`2,009` rules) across **HL7 R4 Core, CA-Baseline 1.2.0, Infoway CA Core 1.1.0, HL7 IPS 1.0.0, and HL7 US Core 8.0.1**, plus dynamic runtime `-ig` loading (`.tgz`, folders, Bundles, StructureDefinitions).
- **Terminology Validation Engine**: Built-in offline grammar validators (UCUM, BCP-47, MIME, ISO-3166), complete CodeSystems (`1,059` systems), precompiled ValueSets (`1,442` ValueSets), `--tx` (`local`, `remote`, `off`), and `--strict-extensible` with two-tier in-memory / SQLite caching.
- **Canadian Localization**: Opt-in CA-Baseline / PS-CA `meta.profile`, all **13 provincial/territorial JHN systems**, `A1A 1A1` postal code FSA checks, and US-extension restrictions (`--no-canadian` to disable).
- **Standard Output Formats**: Text, JSON, self-validating FHIR R4 `OperationOutcome`, **SARIF v2.1.0**, and **JUnit XML**.

## Performance & Benchmarks

Auto-updated on build via [`scripts/benchmark_performance.py`](scripts/benchmark_performance.py) (raw JSON: [`docs/benchmark-results.json`](docs/benchmark-results.json); full methodology: **[Equivalence & Testing](docs/equivalence-and-testing.md)**).

<!-- PERFORMANCE_BENCHMARK_START -->
**Release**: `v0.1.0` | **Python**: `3.13.18` | **Pydantic**: `v2.14.3` (Rust `pydantic-core`) | **Master Suite**: `2,697` pytest items (`8,380+` scenarios, `99.62%` coverage) | **Updated**: `2026-11-14 20:46 UTC`

#### 1. Master Equivalence Dataset (`325` Resources, `146` R4 Types, `10` Invariants & `5` IGs)

| Validator / Mode | Batch (`325`) | Latency | Throughput | Speedup |
| :--- | ---: | ---: | ---: | ---: |
| **FHIRlance — Standard Mode** | **`25.87 ms`** | **`79.6 µs`** | **`12,564 /s`** | **`1,358.0x`** |
| **FHIRlance — FHIR Output (`OperationOutcome`) Mode** | **`29.93 ms`** | **`92.1 µs`** | **`10,859 /s`** | **`1,173.8x`** |
| **Official HL7 Baseline Validator** | `35.13 s` | `108.1 ms` | `9.25 /s` | `1.0x` |

<sub>Standard: `validate_resource()` · FHIR Output: `validate_to_operation_outcome()` · HL7 Baseline: `validator_cli.jar -version 4.0.1 -tx n/a`</sub>

#### 2. High-Volume NDJSON & Test Suite Throughput

| Workload | Volume | Elapsed | Throughput |
| :--- | ---: | ---: | ---: |
| **NDJSON Batch** (`validate_dataset`, JSON) | `1,000` res | **`114.70 ms`** | **`8,718 /s`** |
| **NDJSON Batch** (`--format operation-outcome`) | `1,000` res | **`116.09 ms`** | **`8,614 /s`** |
| **Offline Pytest Suite** (`not hl7_live`) | `2,686` items (`8,380+` cases) | `~12.5 s` | **`~670 cases/s`** |
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

# Validate with offline terminology engine (--tx local default) or remote server fallback
fhirlance path/to/data --no-canadian --tx local --strict-extensible

# Validate with custom runtime IGs (.tgz, folder, or cached package) and explicit profiles
fhirlance path/to/data --no-canadian -ig path/to/custom-ig.tgz --profile http://hl7.org/fhir/StructureDefinition/vitalsigns
```

```python
from fhirlance import validate_dataset, validate_resource, validate_to_operation_outcome

# Validate with offline terminology checks (UCUM, BCP-47, complete CodeSystems & ValueSets)
issues = validate_resource(resource_dict, require_canadian_profile=False, tx="local")
outcome = validate_to_operation_outcome(resource_dict, require_canadian_profile=False, tx="local")
report = validate_dataset("path/to/data", parallel=True, require_canadian_profile=False, tx="local")
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
