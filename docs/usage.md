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
usage: fhirlance [-h] [--profile PROFILE] [-ig IG_SOURCES] [--parallel]
                 [-tx MODE] [--strict-extensible] [--best-practice]
                 [--enforce-must-support]
                 [--unknown-profile {ignore,warning,error}]
                 [--format {text,json,operation-outcome,sarif,junit}]
                 [--operation-outcome] [--json] [-o OUTPUT_PATH]
                 target

usage: fhirlance pkg install [-h] [--cache-dir CACHE_DIR] [--no-deps] package
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
| `--best-practice` | No | `False` | Emit best-practice diagnostic warnings (`dom-6` missing narrative, `Observation.performer`, and `preferred` ValueSet bindings). |
| `--enforce-must-support` | No | `False` | Require all profile `mustSupport` elements to be present (missing `mustSupport` elements fail validation). |
| `--unknown-profile <MODE>` | No | `ignore` | Behavior when a resource declares an unknown profile URL in `meta.profile` or `--profile`: `ignore`, `warning`, or `error`. |
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

# 7. Enable best-practice warnings, mustSupport enforcement, or unknown profile checks
fhirlance path/to/data --best-practice --enforce-must-support --unknown-profile warning
```

### 1.5 Package Manager (`fhirlance pkg install`)

Install FHIR Implementation Guide NPM packages (and their transitive `package.json` dependencies) from the HL7/Simplifier registry into `~/.cache/fhirlance/packages/`:

```bash
# Install a specific IG version and its transitive dependencies
fhirlance pkg install hl7.fhir.uv.ips#1.0.0

# Install into a custom cache directory without transitive dependencies
fhirlance pkg install hl7.fhir.us.core.r4#8.0.1 --cache-dir /path/to/cache --no-deps
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

# 1. Validate a single resource dictionary -> list[str] (with optional terminology & profile flags)
issues = validate_resource(
    resource_dict,
    profile_urls=["http://hl7.org/fhir/StructureDefinition/vitalsigns"],
    ig_sources=["path/to/custom-ig.tgz"],
    tx="local",  # "local", "remote", "off", or TxOptions(mode="local", strict_extensible=True)
    best_practice=False,
    enforce_must_support=False,
    unknown_profile="ignore",  # "ignore", "warning", or "error"
    questionnaire_resource=None,  # Optional Questionnaire dict for QuestionnaireResponse cross-validation
)

# 2. Validate a single resource directly into a FHIR R4 OperationOutcome dict
outcome = validate_to_operation_outcome(
    resource_dict,
    tx="local",
    best_practice=True,
    enforce_must_support=False,
    unknown_profile="warning",
)

# 3. Validate a file (.json / .ndjson) or directory in parallel
report = validate_dataset(
    "path/to/bundles_or_ndjson",
    parallel=True,
    profile_urls=["http://hl7.org/fhir/us/core/StructureDefinition/us-core-patient"],
    ig_sources=["path/to/custom-ig.tgz"],
    tx="local",
    strict_extensible=False,
    best_practice=False,
    enforce_must_support=False,
    unknown_profile="ignore",
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

### 2.1 `ConceptMap` & `$translate` API

FHIRlance exports a local + remote `ConceptMap` `$translate` API directly from `fhirlance`:

```python
from fhirlance import (
    ConceptMapRegistry,
    ConceptMapSpec,
    TranslateMatch,
    TranslateRequest,
    TranslateResult,
    load_ig_concept_maps,
    parse_concept_map,
    translate_code,
)

# Load ConceptMaps from an IG (.tgz, directory, Bundle, or package#version)
registry: ConceptMapRegistry = load_ig_concept_maps(["path/to/custom-ig.tgz"])

# Or parse and register a ConceptMap JSON dict directly
spec: ConceptMapSpec | None = parse_concept_map(concept_map_dict)
if spec is not None:
    registry.register(spec)

# Translate a code (local ConceptMapRegistry first, optional remote TxClient fallback)
result: TranslateResult = translate_code(
    TranslateRequest(
        code="active",
        system="http://hl7.org/fhir/administrative-gender",
        url="http://example.org/ConceptMap/gender-map",
    ),
    registry=registry,
)
if result.result:
    match: TranslateMatch = result.matches[0]
    print(match.equivalence, match.system, match.code, match.display)
```
