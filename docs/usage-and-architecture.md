# FHIRlance CLI, Python API & Architecture Reference

This document provides the complete reference for the **`fhirlance` CLI**, **Python API**, **internal module architecture**, and **local development & code-generation workflows**.

For other topics, see:
- **[Terminology Validation Engine & TX Reference](terminology.md)**
- **[Proof of Functional Equivalence & Test Suite Architecture](equivalence-and-testing.md)**
- **[Build & CI/CD Architecture](ci-and-build.md)**
- **[Architecture & Product Roadmap](roadmap.md)**

---

## 1. CLI Reference (`fhirlance`)

```text
usage: fhirlance [-h] [--no-canadian] [--profile PROFILE] [-ig IG_SOURCES]
                 [--parallel]
                 [--format {text,json,operation-outcome,sarif,junit}]
                 [--operation-outcome] [--json] [-o OUTPUT_PATH]
                 target
```

### 1.1 Positional Arguments & Flags

| Argument / Flag | Repeatable | Default | Description |
| :--- | :---: | :--- | :--- |
| `target` | No | *(Required)* | Path to a FHIR `.json` file (single resource or `Bundle`), `.ndjson` file, or directory containing `.json` / `.ndjson` files. |
| `-h`, `--help` | No | — | Display CLI usage help and exit. |
| `--no-canadian` | No | `False` | Disable Canadian localization checks (`meta.profile` presence, provincial/territorial JHN NamingSystem checks, `A1A 1A1` postal code FSA validation, and US-extension restrictions). |
| `--profile <URL>` | **Yes** | `None` | Additional `StructureDefinition` canonical URL to validate resources against (evaluated alongside any profiles declared in `resource.meta.profile`). |
| `-ig <SOURCE>`, `--ig <SOURCE>` | **Yes** | `None` | Load custom FHIR Implementation Guide(s) at runtime from an NPM tarball (`.tgz` / `.tar.gz`), unpacked directory, `Bundle` / `StructureDefinition` `.json` file, or `~/.fhir/packages` specifier (`<pkg>#<version>` or `<pkg>`). |
| `-tx <MODE>`, `--tx <MODE>` | No | `local` | Terminology validation mode: `local` (offline grammars + complete CodeSystems + precompiled ValueSets), `remote` or `<URL>` (two-tier cache with remote Tx server fallback), or `off` (aliases: `-term`, `--term`). |
| `--strict-extensible` | No | `False` | Treat extensible ValueSet binding violations as errors instead of non-blocking warnings. |
| `--parallel` | No | `False` | Validate multi-file directories, multi-entry `Bundle` JSON files (`>= 64` entries), and multi-line `.ndjson` files (`>= 64` lines) in parallel across worker processes (`ProcessPoolExecutor`). |
| `--format <FMT>` | No | `text` | Output format: `text`, `json`, `operation-outcome`, `sarif`, or `junit` (see table below). |
| `--operation-outcome` | No | `False` | Shorthand alias for `--format operation-outcome` (emits a compliant FHIR R4 `OperationOutcome` JSON resource). |
| `--json` | No | `False` | Shorthand alias for `--format json` (emits the full structured JSON dataset report). |
| `-o <PATH>`, `--output <PATH>` | No | `stdout` | Write the formatted validation report to `<PATH>` (UTF-8) instead of printing to `stdout`. |

### 1.2 Supported Output Formats (`--format`)

| Format | Flag / Shorthand | Output Structure & Use Case |
| :--- | :--- | :--- |
| **`text`** | `--format text` *(default)* | Human-readable summary line (`Validated N resource(s) in X.XXXXs \| valid=... invalid=...`) followed by up to 20 issue descriptions. |
| **`json`** | `--format json` or `--json` | Full JSON summary dictionary (`total_resources`, `valid_resources`, `invalid_resources`, `compliance_rate`, `elapsed_seconds`, and per-resource `issues`). |
| **`operation-outcome`** | `--format operation-outcome` or `--operation-outcome` | Self-validating **FHIR R4 `OperationOutcome`** JSON resource with mapped `IssueType` codes (`structure`, `invariant`, `code-invalid`, `required`, `value`, `exception`), `diagnostics`, and FHIRPath `expression` locations. |
| **`sarif`** | `--format sarif` | **OASIS SARIF v2.1.0** static analysis JSON report with categorized rules (`FHIR001-Structural` through `FHIR005-ParseError`, plus `FHIRLANCE_TERMINOLOGY`) for GitHub Code Scanning and IDE integration. |
| **`junit`** | `--format junit` | **JUnit XML** (`<testsuites>` / `<testcase>` / `<failure>`) report for CI/CD test runners. |

### 1.3 Exit Codes

| Exit Code | Meaning |
| :---: | :--- |
| `0` | All validated resources passed with zero structural, invariant, or profile issues. |
| `1` | One or more resources failed validation or a file could not be parsed. |
| `2` | Invalid CLI arguments or `target` path does not exist (`FileNotFoundError`). |

### 1.4 CLI Examples

```bash
# 1. Validate a directory of FHIR Bundles/NDJSON with base R4 + IG profiles (disable Canadian rules) and multiprocessing
fhirlance path/to/data --no-canadian --parallel

# 2. Emit a standard FHIR R4 OperationOutcome JSON resource to a file
fhirlance path/to/patient.json --no-canadian --operation-outcome -o outcome.json

# 3. Validate terminology: offline local (default), remote fallback, or strict extensible
fhirlance path/to/data --no-canadian --tx local
fhirlance path/to/data --no-canadian --tx remote --strict-extensible
fhirlance path/to/data --no-canadian --tx https://tx.fhir.org/r4

# 4. Validate against explicit StructureDefinition profile URLs (repeatable)
fhirlance path/to/observations.ndjson --no-canadian \
  --profile http://hl7.org/fhir/StructureDefinition/vitalsigns \
  --profile http://hl7.org/fhir/StructureDefinition/heartrate

# 5. Load custom runtime Implementation Guides (.tgz tarball, folder, or cached package)
fhirlance path/to/data --no-canadian \
  -ig path/to/custom-ig.tgz \
  -ig hl7.fhir.uv.ips#1.0.0 \
  --format operation-outcome -o ips-outcome.json

# 6. Generate SARIF v2.1.0 or JUnit XML reports for CI pipelines
fhirlance path/to/data --no-canadian --format sarif -o results.sarif.json
fhirlance path/to/data --no-canadian --format junit -o junit-report.xml
```

---

## 2. Python API Reference

```python
from fhirlance import (
    TxOptions,
    dataset_to_junit_xml,
    dataset_to_operation_outcome,
    dataset_to_sarif,
    format_dataset_report,
    register_ig,
    validate_dataset,
    validate_resource,
    validate_to_operation_outcome,
)

# 1. Validate a single resource dictionary -> list[str] (with optional terminology options)
issues = validate_resource(
    resource_dict,
    require_canadian_profile=False,
    profile_urls=["http://hl7.org/fhir/StructureDefinition/vitalsigns"],
    ig_sources=["path/to/custom-ig.tgz"],
    tx="local",  # "local", "remote", "off", or TxOptions(mode="local", strict_extensible=True)
)

# 2. Validate a single resource directly into a FHIR R4 OperationOutcome dict
outcome = validate_to_operation_outcome(
    resource_dict,
    require_canadian_profile=False,
    tx="local",
)

# 3. Validate a file (.json / .ndjson) or directory in parallel
report = validate_dataset(
    "path/to/bundles_or_ndjson",
    parallel=True,
    require_canadian_profile=False,
    profile_urls=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"],
    ig_sources=["path/to/custom-ig.tgz"],
    tx="local",
    strict_extensible=False,
)

# Note: report separates blocking errors from non-blocking diagnostic warnings:
# report["issues"]   -> dict[file_name, list[error_str]]
# report["warnings"] -> dict[file_name, list[warning_str]]
# Warning-only resources remain counted in report["valid_resources"].

# 4. Format a dataset report into OperationOutcome, SARIF v2.1.0, or JUnit XML
oo_dict = dataset_to_operation_outcome(report)
sarif_dict = dataset_to_sarif(report)
junit_xml_str = dataset_to_junit_xml(report)
formatted_str = format_dataset_report(report, output_format="operation-outcome")

# 5. Register a custom IG globally for the current process
register_ig("path/to/custom-ig.tgz")
```

---

## 3. Package Architecture (`src/fhirlance/`)

| Module | Role & Responsibilities |
| :--- | :--- |
| [`base.py`](../src/fhirlance/base.py) | `FHIRBaseModel` (pure Rust `pydantic-core` hot path with `extra="forbid"`), `ExtensionBase` (`ext-1`), `DomainResourceBase`, and strict FHIR R4 primitive types (`FHIRDate`, `FHIRDateTime`, `FHIRInstant`, `FHIRTime`, `FHIRId`, `FHIRCode`, `FHIRPositiveInt`, `FHIRUnsignedInt`). |
| [`types.py`](../src/fhirlance/types.py) & [`resources.py`](../src/fhirlance/resources.py) | Auto-generated Pydantic v2 models for all **39 complex datatypes**, **146 FHIR R4 resources**, and **473 BackboneElement** sub-models (**659 classes**, **8,350 typed fields**, **186 `[x]` choice groups**). Never hand-edit. |
| [`profiles.py`](../src/fhirlance/profiles.py) | Auto-generated Implementation Guide profile constraint definitions (**183 profiles**, **2,009 rules** across 5 IGs). Never hand-edit. |
| [`profile_engine.py`](../src/fhirlance/profile_engine.py) | Typed, pre-compiled `StructureDefinition` constraint evaluator (`required`, `forbidden`, `max_one`, `fixed[x]`, `pattern[x]`, `[x]` type narrowing, `Reference.targetProfile`, `required` ValueSet bindings, and discriminator slicing). |
| [`ig_loader.py`](../src/fhirlance/ig_loader.py) | Runtime Implementation Guide loader supporting `.tgz` tarballs, unpacked directories, `Bundle`s, `StructureDefinition`s, and `~/.fhir/packages` semver resolution with `baseDefinition` inheritance merging. |
| [`invariants.py`](../src/fhirlance/invariants.py) | Core FHIRPath invariant dispatchers (`txt-1`, `pat-1`, `obs-6`, `obs-7`, `con-4`, `bdl-1`, `bdl-3`, `bdl-4`, `bdl-7`). |
| [`primitive_extensions.py`](../src/fhirlance/primitive_extensions.py) | Lazy `_primitive` JSON extension fallback invoked only when `extra="forbid"` encounters a `_field` companion property. |
| [`canadian.py`](../src/fhirlance/canadian.py) | Pan-Canadian profile and patient localization rules (13 provincial/territorial JHN NamingSystems, `A1A 1A1` postal code FSA validation, and US-extension bans). |
| [`formatters.py`](../src/fhirlance/formatters.py) | Self-validating FHIR R4 `OperationOutcome`, OASIS SARIF v2.1.0, JUnit XML, JSON, and human-readable text report formatters. |
| [`resource_validator.py`](../src/fhirlance/resource_validator.py) | Single-resource validation orchestrator and depth-guarded (`max_depth=16`) recursive `Bundle.entry[].resource` and `DomainResource.contained[]` validator. |
| [`terminology.py`](../src/fhirlance/terminology.py) | Offline grammar validation (UCUM, BCP-47, MIME, ISO-3166), local complete CodeSystems, ValueSet binding validation, and two-tier L1 in-memory / L2 SQLite remote caching client. |
| [`dataset.py`](../src/fhirlance/dataset.py) | Strict JSON (`NaN`/`Infinity`-rejecting) loader and sequential/multi-process (`ProcessPoolExecutor`) dataset runner for `.json`, `.ndjson`, and directories. |
| [`validator.py`](../src/fhirlance/validator.py) | Public validation facade re-exported by `fhirlance`. |
| [`cli.py`](../src/fhirlance/cli.py) | `fhirlance` command-line entrypoint. |

---

## 4. Build, Codegen & Local Quality Gate

### 4.1 Schema Compilation & Benchmark Scripts (`scripts/`)

```bash
# Regenerate types.py, resources.py, and profiles.py from ~/.fhir/packages
python scripts/generate_models.py

# Run performance benchmarks and update README.md, docs/equivalence-and-testing.md, and docs/benchmark-results.json
python scripts/benchmark_performance.py --update-docs

# Re-run live HL7 validator_cli.jar baseline benchmark and update docs
python scripts/benchmark_performance.py --run-hl7-live --update-docs
```

### 4.2 Local Development & Quality Gate

Install development dependencies (`ruff`, `mypy`, `pytest-cov`, `hypothesis`, `pip-audit`, `build`, `twine`):
```bash
pip install -e ".[dev]"
```

Run the full local quality gate:
```bash
ruff check .
ruff format --check .
mypy
pytest -m "not hl7_live" --cov --cov-report=term-missing --cov-fail-under=95
pip-audit
```

Run live HL7 `validator_cli.jar` equivalence tests (requires Java + `validator_cli.jar`):
```bash
pytest -m hl7_live -v -s
```
