# FHIRlance

[![CI](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/ci.yml)
[![CodeQL](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml/badge.svg)](https://github.com/damsonaldson/FHIRlance/actions/workflows/codeql.yml)

High-performance **FHIR R4 structural & Implementation Guide profile validator** backed by Pydantic v2 (`pydantic-core` in Rust).

## Coverage
- **Full FHIR R4 Base Spec**: All **146 base resources** and **39 complex datatypes** (`extra="forbid"`, strict primitive patterns/types, non-empty arrays, `[x]` choice exclusivity, `_primitive` JSON extensions, `Extension` `ext-1`, recursive `Bundle.entry[].resource` and `contained[]` validation, and core FHIRPath invariants).
- **Multi-IG Profile Engine**: Pre-compiled constraints with `baseDefinition` inheritance across **HL7 R4 Core, CA-Baseline 1.2.0, Infoway CA Core, HL7 IPS 1.0.0, and HL7 US Core 8.0.1** (cardinality, `max=0` forbidden elements, `fixed[x]`, `pattern[x]`, `[x]` type narrowing, `Reference.targetProfile`, `required` bindings, and slicing).
- **Canadian Profile Rules**: Optional CA-Baseline / PS-CA `meta.profile`, provincial JHN, postal code, and US-extension checks (`require_canadian_profile=True/False`).

## Architecture
- `base.py`: `FHIRBaseModel` (pure Rust `pydantic-core` hot path), `ExtensionBase` (`ext-1`), `DomainResourceBase`, strict R4 primitives.
- `types.py` & `resources.py`: Auto-generated Pydantic v2 models (never edit by hand).
- `profiles.py`: Auto-generated IG profile constraint definitions (never edit by hand).
- `profile_engine.py`: Typed, pre-compiled StructureDefinition constraint evaluator.
- `invariants.py`: Core FHIRPath invariant dispatchers (`txt-1`, `pat-1`, `obs-6`, `obs-7`, `con-4`, `bdl-1`, `bdl-3`, `bdl-4`, `bdl-7`).
- `primitive_extensions.py`: Lazy `_primitive` JSON extension fallback invoked only when needed.
- `canadian.py`: Pan-Canadian profile and patient localization rules.
- `resource_validator.py`: Single-resource validation orchestrator and depth-guarded recursion.
- `dataset.py`: Strict JSON (`NaN`/`Infinity`-rejecting) and sequential/parallel dataset runner.
- `validator.py`: Backward-compatible public validation facade.
- `cli.py`: `fhirlance` CLI entrypoint.

## Usage

### Python API
```python
from fhirlance import validate_resource, validate_dataset

issues = validate_resource(resource_dict, require_canadian_profile=False)
report = validate_dataset("path/to/bundles_or_ndjson", parallel=True)
```

### CLI
```bash
fhirlance path/to/data --no-canadian --parallel
```

### Regenerating Models from Cached HL7 Packages
```bash
python scripts/generate_models.py
```

## Development & Quality Checks
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
pytest -m hl7_live -v
```

## CI & Automated PR Reviews
- `.github/workflows/ci.yml`: Enforces Ruff lint/format, strict Mypy, multi-OS/Python matrix (`ubuntu-latest` + `windows-latest`, Python 3.10–3.13) with a 95% branch coverage gate, `pip-audit`, distribution build verification, and manual `workflow_dispatch` live HL7 equivalence.
- `.github/workflows/codeql.yml`: Static security analysis via GitHub CodeQL.
- `.github/workflows/ai-review.yml`: Optional free-tier Gemini API automated PR code review (add a free Google AI Studio key as the `GEMINI_API_KEY` repository secret).

## License
Copyright (c) 2026 **Brightwood Consulting Group Limited**.

Licensed under the **Creative Commons Attribution-NonCommercial 4.0 International License ([CC BY-NC 4.0](LICENSE))** — free to use, share, and adapt for **non-commercial purposes only** with attribution. For commercial licensing inquiries, please contact Brightwood Consulting Group Limited.

