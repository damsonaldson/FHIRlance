# FHIRlance

[![CI](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml)
[![CodeQL](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml)

High-performance **FHIR R4 structural & Implementation Guide profile validator** backed by Pydantic v2 (`pydantic-core` in Rust).

## Documentation
- **[CLI & Python API Reference](docs/usage.md)** — Full CLI flags, output formats, exit codes, and Python API examples.
- **[Package Architecture & Development Reference](docs/architecture.md)** — Internal module breakdown, schema codegen, and local quality-gate workflow.
- **[Terminology Validation Engine & TX Reference](docs/terminology.md)** — Offline grammars (UCUM, BCP-47, MIME, ISO-3166), 3,061 complete CodeSystems, 7,139 ValueSets, `ConceptMap` `$translate`, `--tx` modes, and L1/SQLite caching.
- **[Proof of Functional Equivalence & Test Suite](docs/equivalence-and-testing.md)** — HL7 `validator_cli.jar` equivalence matrix and test catalog (`3,039` items / `97.17%` coverage).
- **[Build & CI/CD Architecture](docs/ci-and-build.md)** — Ahead-of-time schema compilation, security gates, and cross-platform CI pipeline.
- **[Architecture & Product Roadmap](docs/roadmap.md)** — Footprint-prioritized roadmap (`v0.1.0`–`v1.0.0`) and HAPI FHIR / Smile CDR integration design.

## Coverage (TL;DR)
- **Full FHIR R4 Base Spec**: All **146 resources** and **39 complex datatypes** (`661` generated Pydantic v2 models incl. `SimpleQuantity`, 32-bit `FHIRInteger`, 1 MB `FHIRString`, `_primitive` extensions, `ext-1`, `38` base invariant sets / `91` rules, zero-`exec` AST-combinator FHIRPath, `Questionnaire`/`QuestionnaireResponse`, and recursive `Bundle` / `contained[]` validation).
- **Multi-IG Profile Engine**: **198 pre-compiled profiles** (`185` resource + `13` complex-type profiles, `3,579` rules, `441` extensions) across **HL7 R4 Core (`49`), CA-Baseline (`28`), CA Core (`34`), UV IPS (`33`), and US Core (`54`)**, plus dynamic runtime `-ig` loading (`.tgz`, folders, Bundles, StructureDefinitions), transitive `package.json` dependencies, `fhirlance pkg install`, `--enforce-must-support`, `--best-practice`, and `--unknown-profile`.
- **Terminology Validation Engine**: Built-in offline grammar validators (UCUM, BCP-47, MIME, ISO-3166), complete CodeSystems (`3,061` systems incl. `hl7.terminology.r4`), precompiled ValueSets (`7,139` ValueSets with `url|version` indexing, `CodeSystem.supplements`, `compose.include.filter`, `compose.exclude`, `expansion.contains`), `ConceptMap` & `$translate`, `--tx` (`local`, `remote`, `off`), and `--strict-extensible` with two-tier in-memory / SQLite caching.
- **Standard Output Formats**: Text, JSON, self-validating FHIR R4 `OperationOutcome`, **SARIF v2.1.0**, and **JUnit XML**.

## Performance & Benchmarks

Auto-updated on build via [`scripts/benchmark_performance.py`](scripts/benchmark_performance.py) (raw JSON: [`docs/benchmark-results.json`](docs/benchmark-results.json); full methodology: **[Equivalence & Testing](docs/equivalence-and-testing.md)**).

<!-- PERFORMANCE_BENCHMARK_START -->
**Release**: `v0.1.0` | **Python**: `3.13.18` | **Pydantic**: `v2.14.3` (Rust `pydantic-core`) | **Master Suite**: `3,039` pytest items (`3,029` offline, `97.17%` coverage) | **Updated**: `2026-11-17 13:44 UTC`

#### 1. Master Equivalence Dataset (`342` Resources, `146` R4 Types, `10` Invariants & `5` IGs)

| Validator / Mode | Batch (`342`) | Latency | Throughput | Speedup |
| :--- | ---: | ---: | ---: | ---: |
| **FHIRlance — Standard Mode** | **`41.71 ms`** | **`122.0 µs`** | **`8,199 /s`** | **`842.2x`** |
| **FHIRlance — FHIR Output (`OperationOutcome`) Mode** | **`45.31 ms`** | **`132.5 µs`** | **`7,548 /s`** | **`775.4x`** |
| **Official HL7 Baseline Validator** | `35.13 s` | `102.7 ms` | `9.74 /s` | `1.0x` |

<sub>Standard: `validate_resource()` · FHIR Output: `validate_to_operation_outcome()` · HL7 Baseline: `validator_cli.jar -version 4.0.1 -tx n/a`</sub>

#### 2. High-Volume NDJSON & Test Suite Throughput

| Workload | Volume | Elapsed | Throughput |
| :--- | ---: | ---: | ---: |
| **NDJSON Batch** (`validate_dataset`, JSON) | `1,000` res | **`152.93 ms`** | **`6,539 /s`** |
| **NDJSON Batch** (`--format operation-outcome`) | `1,000` res | **`156.25 ms`** | **`6,400 /s`** |
| **Offline Pytest Suite** (`not hl7_live`) | `3,029` items (`97.17%` cov) | `25.66 s` | **`118.0 items/s`** |
<!-- PERFORMANCE_BENCHMARK_END -->

## HL7 Equivalence & Testing (TL;DR)
- **Live `validator_cli.jar` Parity**: Verified against HL7's official Java reference validator (`-version 4.0.1 -tx n/a`) via `pytest -m hl7_live` (local JDK 17 + `FHIR_VALIDATOR_JAR` or the `hl7-equivalence` CI `workflow_dispatch` job) across all 146 R4 resource types, invariants, primitives, and IG profiles with **zero equivalence mismatches**.
- **Exhaustive Test Matrix**: **3,039 pytest items** (`3,029` offline + `10` `hl7_live`) at **97.17% branch coverage**, plus Hypothesis property-based fuzzing.
- **Details**: **[Proof of Functional Equivalence & Test Suite Architecture](docs/equivalence-and-testing.md)**.

## Quick Start (TL;DR)

```bash
# Install (with dev tools)
pip install -e ".[dev]"

# Validate a file or directory (parallel, base R4 + IG profiles, OperationOutcome output)
fhirlance path/to/data --parallel --operation-outcome -o outcome.json

# Validate with offline terminology engine (--tx local default) or remote server fallback
fhirlance path/to/data --tx local --strict-extensible

# Validate with custom runtime IGs (.tgz, folder, or cached package) and explicit profiles
fhirlance path/to/data -ig path/to/custom-ig.tgz --profile http://hl7.org/fhir/StructureDefinition/vitalsigns

# Install an IG package (with transitive package.json dependencies) to ~/.cache/fhirlance/packages/
fhirlance pkg install hl7.fhir.us.core.r4#8.0.1

# Validate with best-practice hints, Must Support enforcement, and unknown-profile handling
fhirlance path/to/data --best-practice --enforce-must-support --unknown-profile warning
```

```python
from fhirlance import validate_dataset, validate_resource, validate_to_operation_outcome

# Validate with offline terminology checks (UCUM, BCP-47, complete CodeSystems & ValueSets)
issues = validate_resource(resource_dict, tx="local")
outcome = validate_to_operation_outcome(resource_dict, tx="local")
report = validate_dataset("path/to/data", parallel=True, tx="local")
```

- **Full CLI flags, exit codes & Python API**: **[CLI & Python API Reference](docs/usage.md)**.

## Architecture & CI/CD (TL;DR)
- **Ahead-of-Time Codegen + Rust Hot Path**: `scripts/generate_models.py` compiles HL7 FHIR packages into `types.py`, `resources.py`, and `profiles.py` with zero runtime schema I/O and no Python `@model_validator(mode="before")` on `FHIRBaseModel`.
- **Quality, Security & Release Gates**: Enforces pre-commit hooks (`.pre-commit-config.yaml`), `ruff`, strict `mypy` (`pydantic.mypy`), `pytest --cov-fail-under=95` across Linux/Windows (Python 3.10–3.13), `pip-audit`, CodeQL, clean-room wheel smoke tests, and tag-triggered PyPI Trusted Publishing (`release.yml`).
- **Details**: **[Package Architecture & Development Reference](docs/architecture.md)** and **[Build & CI/CD Architecture](docs/ci-and-build.md)**.

## Roadmap & HAPI FHIR / Smile CDR Integration (TL;DR)
- **Baseline (`v0.1.0` — Done)**: All 146 R4 resources, 39 datatypes, 183 IG profiles, dynamic `-ig`, local/SQLite TX (`hl7.terminology.r4` + 5 IGs), and `OperationOutcome`/SARIF/JUnit output.
- **Tier 1 (`v0.2.0` — Done)**: Extension `StructureDefinition`s, full slicing (all 5 discriminators, slice `max`, `closed`/`ordered`, nested sub-slicing), `Bundle` reference/`targetProfile` graph & outer `Bundle` validation, and complex datatype bindings.
- **Tier 2 (`v0.3.0` — Done)**: Core R4 conformance/form/terminology resources (`Questionnaire`/`QuestionnaireResponse` `que-*`/`enableWhen`/`answerOption`, `CapabilityStatement`/`OperationDefinition`/`SearchParameter`, `ConceptMap` `$translate`, `Subscription`, `TestScript`, `StructureMap`, `GraphDefinition`, `MolecularSequence`, `MedicinalProduct*`, `VerificationResult`), zero-`exec` AST-combinator FHIRPath (`fhirpath.py`) + `38` base invariant sets (`91` rules), `maxLength`/`minValue`/`maxValue`/`type.profile`, transitive `package.json` IG dependencies & `fhirlance pkg install`, versioned canonicals (`url|version`), `CodeSystem.supplements`, `compose.include.filter`/`exclude`/`expansion.contains`, `--best-practice`, `--enforce-must-support`, and `--unknown-profile`.
- **Tier 3 (`v0.4.0` — Next)**: `fhirlance serve` persistent `$validate` daemon (Unix Domain Sockets & HTTP), HAPI FHIR / Smile CDR raw-byte interceptor, Envoy/NGINX edge filter, and `mmap` streaming NDJSON.
- **Tier 4 (`v1.0.0` — Long-Term)**: Multi-version `R4B`/`R5` codegen (Python-first; native Rust C-ABI / Panama FFI deferred unless zero-sidecar JVM embedding is required).
- **Details**: **[Architecture & Product Roadmap](docs/roadmap.md)**.

## License
Copyright (c) 2026 **Brightwood Consulting Group Limited**. Licensed under **[CC BY-NC 4.0](LICENSE)** (free for non-commercial use with attribution).
