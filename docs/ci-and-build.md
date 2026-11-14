# FHIRlance Build & CI/CD Architecture

This document explains how **FHIRlance** compiles HL7 FHIR R4 specifications into zero-I/O Pydantic v2 models, enforces local developer quality gates, and validates, audits, packages, and smoke-tests distributions in GitHub Actions.

![FHIRlance Build, Code Generation & CI/CD Architecture](assets/ci-build-pipeline.svg)

---

## End-to-End Pipeline Flow (Mermaid)

```mermaid
flowchart LR
    subgraph Phase1["1. Offline Schema Compilation & Local Gate"]
        direction TB
        PKGS["HL7 FHIR Packages (~/.fhir/packages)<br/>• R4 Core 4.0.1<br/>• CA-Baseline 1.2.0 & Infoway 1.1.0<br/>• HL7 IPS 1.0.0 & US Core 8.0.1"]
        CODEGEN["Schema Compiler<br/>(scripts/generate_models.py)"]
        GEN["Generated Modules (Zero Runtime I/O)<br/>• src/fhirlance/types.py (39 types)<br/>• src/fhirlance/resources.py (146 resources)<br/>• src/fhirlance/profiles.py (IG constraints)"]
        CORE["Handwritten Validation Engine<br/>(base.py, profile_engine.py, invariants.py,<br/>canadian.py, resource_validator.py, cli.py)"]
        PRE["Local Pre-Commit Gate<br/>(.pre-commit-config.yaml)<br/>• ruff --fix & ruff-format<br/>• mypy (strict + pydantic.mypy)"]

        PKGS --> CODEGEN --> GEN --> PRE
        CORE --> PRE
    end

    subgraph Phase2["2. GitHub Actions: Parallel Fast Gates"]
        direction TB
        QUAL["CI: quality (ubuntu-latest, Py 3.13)<br/>• ruff check . (McCabe <= 10)<br/>• ruff format --check .<br/>• mypy (strict)"]
        SEC["CI: security (ubuntu-latest, Py 3.13)<br/>• pip-audit (PyPA CVE database)"]
        CODEQL["CodeQL SAST (codeql.yml)<br/>• github/codeql-action (Python)<br/>• Push, PR & Weekly Cron"]
        AIREVIEW["AI PR Review (ai-review.yml)<br/>• Diffs handwritten code only<br/>• Checks SOLID & Rust hot-path rules"]
    end

    subgraph Phase3["3. Cross-Platform Test Matrix & HL7 Parity"]
        direction TB
        MATRIX["CI: test (8-Job Matrix)<br/>• OS: ubuntu-latest, windows-latest<br/>• Python: 3.10, 3.11, 3.12, 3.13<br/>• pytest -m 'not hl7_live'<br/>• >= 95% Branch Coverage Gate<br/>• Uploads coverage.xml artifact"]
        HL7["CI: hl7-equivalence (workflow_dispatch)<br/>• Temurin JDK 17 + Python 3.13<br/>• Downloads official validator_cli.jar<br/>• pytest -m hl7_live"]
    end

    subgraph Phase4["4. Benchmark, Package Build & Clean-Room Smoke Test"]
        direction TB
        BENCH["Build Benchmark & Docs Sync<br/>• python scripts/benchmark_performance.py --update-docs<br/>• Updates README.md, docs/equivalence-and-testing.md,<br/>  and docs/benchmark-results.json"]
        BUILD["CI: build (ubuntu-latest, Py 3.13)<br/>• python -m build (sdist + wheel)<br/>• twine check dist/*"]
        SMOKE["Clean-Room Venv Smoke Test<br/>• /tmp/smoke-venv pip install dist/*.whl<br/>• fhirlance --help<br/>• Assert len(RESOURCE_MODELS) == 146"]
        BENCH --> BUILD --> SMOKE
    end

    PRE -->|"git push / PR"| QUAL
    PRE -->|"git push / PR"| SEC
    PRE -->|"git push / PR"| CODEQL
    PRE -->|"pull_request"| AIREVIEW
    QUAL --> MATRIX
    MATRIX --> BUILD
```

---

## Stage-by-Stage Breakdown

### Phase 1: Offline Schema Compilation (`scripts/generate_models.py`)
FHIRlance avoids parsing multi-megabyte FHIR StructureDefinition JSON files at runtime. Instead, schema compilation happens ahead-of-time via `scripts/generate_models.py`:

1. **Input Packages (`~/.fhir/packages/`)**:
   - `hl7.fhir.r4.core#4.0.1` (Base FHIR R4 specification)
   - `hl7.fhir.ca.baseline#1.2.0` (Canadian Baseline Implementation Guide)
   - `ca.infoway.io.core#1.1.0-dft-preballot` (Canada Health Infoway CA Core+)
   - `hl7.fhir.uv.ips#1.0.0` (HL7 International Patient Summary)
   - `hl7.fhir.us.core.r4#8.0.1` (HL7 US Core)
2. **Generated Artifacts (Committed to `src/fhirlance/`)**:
   - `types.py`: All **39 FHIR R4 complex datatypes** (`Coding`, `CodeableConcept`, `Identifier`, `Period`, `Reference`, etc.).
   - `resources.py`: All **146 FHIR R4 base resources** (`Patient`, `Observation`, `Bundle`, etc.) subclasses of `DomainResourceBase` / `FHIRBaseModel` (`extra="forbid"`, strict R4 regex primitives).
   - `profiles.py`: Pre-compiled Implementation Guide profile constraints with resolved `baseDefinition` inheritance chains (cardinality, `max=0` forbidden elements, `fixed[x]`, `pattern[x]`, `[x]` type narrowing, `Reference.targetProfile`, `binding_specs` preserving parent `required` strength, and slicing definitions), plus precompiled terminology tables: **1,059 `COMPLETE_CODE_SYSTEMS`**, **1,442 `VALUE_SET_SPECS`**, and **146 `BASE_RESOURCE_BINDINGS`**.

> [!IMPORTANT]
> **Engineering Guardrails**:
> 1. **Never hand-edit** `src/fhirlance/types.py`, `src/fhirlance/resources.py`, or `src/fhirlance/profiles.py`. Always regenerate via `python scripts/generate_models.py`.
> 2. **Keep the hot path in Rust (`pydantic-core`)**: `FHIRBaseModel` intentionally omits `@model_validator(mode="before")` so standard JSON payloads validate at native Rust speeds; `_primitive` JSON extensions are handled lazily by `primitive_extensions.py` only when extra keys are rejected.

---

### Phase 2: Local Developer & Pre-Commit Gate (`.pre-commit-config.yaml`)
Before commits leave a developer workstation, `pre-commit` enforces:
- **Repository Hygiene**: `trailing-whitespace`, `end-of-file-fixer`, `check-toml`, `check-yaml`, `check-merge-conflict`, and `check-added-large-files` (`--maxkb=1024`).
- **Linting & Formatting**: `ruff --fix` and `ruff-format` (targeting Python 3.10+, 100-char line length, McCabe complexity ≤ 10, max 5 arguments, max 10 branches, max 35 statements per function).
- **Static Typing**: `mypy` in `strict = true` mode with the `pydantic.mypy` plugin enabled across `src/fhirlance`, `scripts`, and `tests`.

---

### Phase 3: Continuous Integration & Security Workflows (`.github/workflows/`)

#### 1. Main CI Pipeline (`.github/workflows/ci.yml`)
Triggered on `push` to `main`, `pull_request` targeting `main`, and manual `workflow_dispatch`. Uses concurrency cancellation (`cancel-in-progress: true`) and read-only `GITHUB_TOKEN` permissions (`contents: read`).

| Job ID | Runner / Matrix | Dependencies | What It Verifies |
| :--- | :--- | :--- | :--- |
| **`quality`** | `ubuntu-latest` (Python 3.13) | None | Runs `ruff check .`, `ruff format --check .`, and strict `mypy`. Acts as a fast fail gate (~23s) before launching the 8-job test matrix. |
| **`security`** | `ubuntu-latest` (Python 3.13) | None | Runs `pip-audit --progress-spinner off` (~22s) to audit all installed runtime and dev dependencies against the PyPA advisory database for known CVEs. |
| **`test`** | `ubuntu-latest`, `windows-latest` × Python `3.10`, `3.11`, `3.12`, `3.13` (8 jobs) | `needs: quality` | Runs `pytest -m "not hl7_live" --cov --cov-report=xml --cov-report=term-missing --cov-fail-under=95`. Enforces **≥ 95% branch coverage** across all handwritten modules in `src/fhirlance` and uploads `coverage.xml` from `ubuntu-latest` / Python 3.13 (14-day retention). |
| **`build`** | `ubuntu-latest` (Python 3.13) | `needs: [quality, test]` | Runs `python scripts/benchmark_performance.py --update-docs` to refresh the Performance section in `README.md`, `docs/equivalence-and-testing.md`, and `docs/benchmark-results.json`, builds sdist (`.tar.gz`) and wheel (`.whl`) via `python -m build`, validates package metadata with `twine check dist/*`, uploads the `benchmark-results` artifact, and runs a **clean-room smoke test** inside `/tmp/smoke-venv` (`pip install dist/*.whl`, `fhirlance --help`, and `assert len(fhirlance.RESOURCE_MODELS) == 146`). |
| **`hl7-equivalence`** | `ubuntu-latest` (Python 3.13 + Temurin JDK 17) | `if: github.event_name == 'workflow_dispatch'` | Downloads the latest official HL7 `validator_cli.jar` from `hapifhir/org.hl7.fhir.core`, runs `pytest -m hl7_live -v -s` to verify equivalence against the reference Java validator across all 146 R4 resources, and runs `python scripts/benchmark_performance.py --run-hl7-live --update-docs`. |

#### 2. Static Application Security Testing (`.github/workflows/codeql.yml`)
- Runs GitHub **CodeQL** analysis for Python (`github/codeql-action@v3`) on every push to `main`, every pull request targeting `main`, and on a weekly schedule (`23 4 * * 1` — Mondays at 04:23 UTC).
- Reports findings directly to the repository's GitHub **Security** tab (`security-events: write`).

#### 3. Automated AI PR Code Review (`.github/workflows/ai-review.yml`)
- Triggered on `pull_request` (`opened`, `synchronize`, `reopened`) from same-repository branches.
- Computes a unified git diff excluding auto-generated files (`types.py`, `resources.py`, `profiles.py`) and submits it to the Gemini API (`GEMINI_API_KEY` secret) to review for FHIR R4 semantics, SOLID/Clean Code adherence, and the Rust `pydantic-core` hot-path guardrails, posting the review directly as a PR comment.

#### 4. Automated Dependency Maintenance (`.github/dependabot.yml`)
- Configured for weekly automated pull requests across both **`pip`** (`pyproject.toml`) and **`github-actions`** (`.github/workflows/*.yml`).
