# FHIRlance CLI & Python API Reference

This document provides the complete usage reference for the **`fhirlance` CLI** and **Python API**.

For other topics, see:
- **[Package Architecture & Development Workflow](architecture.md)**
- **[Terminology Validation Engine & TX Reference](terminology.md)**
- **[Proof of Functional Equivalence & Test Suite Architecture](equivalence-and-testing.md)**
- **[Build & CI/CD Architecture](ci-and-build.md)**
- **[Architecture & Product Roadmap](roadmap.md)**

---

## 1. CLI Reference (`fhirlance`)

```text
usage: fhirlance [-h] [--profile PROFILE] [-ig IG_SOURCES]
                 [-tx MODE] [--strict-extensible] [--parallel]
                 [--format {text,json,operation-outcome,sarif,junit}]
                 [--operation-outcome] [--json] [-o OUTPUT_PATH]
                 target
```

### 1.1 Positional Arguments & Flags

| Argument / Flag | Repeatable | Default | Description |
| :--- | :---: | :--- | :--- |
| `target` | No | *(Required)* | Path to a FHIR `.json` file (single resource or `Bundle`), `.ndjson` file, or directory containing `.json` / `.ndjson` files. |
| `-h`, `--help` | No | — | Display CLI usage help and exit. |
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
# 1. Validate a directory of FHIR Bundles/NDJSON with base R4 + IG profiles and multiprocessing
fhirlance path/to/data --parallel

# 2. Emit a standard FHIR R4 OperationOutcome JSON resource to a file
fhirlance path/to/patient.json --operation-outcome -o outcome.json

# 3. Validate terminology: offline local (default), remote fallback, or strict extensible
fhirlance path/to/data --tx local
fhirlance path/to/data --tx remote --strict-extensible
fhirlance path/to/data --tx https://tx.fhir.org/r4

# 4. Validate against explicit StructureDefinition profile URLs (repeatable)
fhirlance path/to/observations.ndjson \
  --profile http://hl7.org/fhir/StructureDefinition/vitalsigns \
  --profile http://hl7.org/fhir/StructureDefinition/heartrate

# 5. Load custom runtime Implementation Guides (.tgz tarball, folder, or cached package)
fhirlance path/to/data \
  -ig path/to/custom-ig.tgz \
  -ig hl7.fhir.uv.ips#1.0.0 \
  --format operation-outcome -o ips-outcome.json

# 6. Generate SARIF v2.1.0 or JUnit XML reports for CI pipelines
fhirlance path/to/data --format sarif -o results.sarif.json
fhirlance path/to/data --format junit -o junit-report.xml
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
    profile_urls=["http://hl7.org/fhir/StructureDefinition/vitalsigns"],
    ig_sources=["path/to/custom-ig.tgz"],
    tx="local",  # "local", "remote", "off", or TxOptions(mode="local", strict_extensible=True)
)

# 2. Validate a single resource directly into a FHIR R4 OperationOutcome dict
outcome = validate_to_operation_outcome(
    resource_dict,
    tx="local",
)

# 3. Validate a file (.json / .ndjson) or directory in parallel
report = validate_dataset(
    "path/to/bundles_or_ndjson",
    parallel=True,
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
