# Changelog

All notable changes to **FHIRlance** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.3.0] - 2026-11-27

### Added (Tier 2 — Core R4 Conformance, Forms, Terminology & IG Ecosystem)
- **Specialized FHIR R4 Resources & Forms**:
  - Added [`questionnaire.py`](src/fhirlance/questionnaire.py) for `Questionnaire` (`enableWhen`, `answerOption`, `answerValueSet`) and `QuestionnaireResponse` cross-validation via `Bundle`, `contained[]`, and explicit `questionnaire_resource`.
  - Added [`specialized_invariants.py`](src/fhirlance/specialized_invariants.py) enforcing specialized resource invariants (`Questionnaire` `que-1`–`que-13`, `QuestionnaireResponse` `qrs-1`, `CapabilityStatement`, `OperationDefinition`, `SearchParameter`, `ConceptMap`, `TestScript`, `StructureMap`, `MolecularSequence`, and `Subscription`), alongside full R4 structural models in `resources.py` for `GraphDefinition`, `MedicinalProduct*`, and `VerificationResult`.
  - Added [`conceptmap.py`](src/fhirlance/conceptmap.py) providing `ConceptMap` parsing, `ConceptMapRegistry`, and local-first / remote-fallback `$translate` (`translate_code`), paired with IG `ConceptMap` extraction (`load_ig_concept_maps`) in [`ig_loader.py`](src/fhirlance/ig_loader.py).
- **Zero-`exec` AST-Combinator FHIRPath & Best Practices**:
  - Added [`fhirpath.py`](src/fhirlance/fhirpath.py) pure-Python AST-combinator FHIRPath R4 evaluator wired into [`invariants.py`](src/fhirlance/invariants.py) (`38` base invariant sets / `91` rules) and [`profile_engine.py`](src/fhirlance/profile_engine.py).
  - Added `--best-practice` / `best_practice=True` flag for non-blocking HL7 best-practice diagnostics (`dom-6` narrative, `Observation.performer`, `preferred` ValueSet bindings).
- **Remaining `ElementDefinition` Constraints & Base Model Hardening**:
  - Added enforcement for `maxLength`, `minValue[x]` / `maxValue[x]`, `type.profile` (profiled datatypes including `SimpleQuantity`), empty-list `min >= 1`, 32-bit `FHIRInteger`, 1 MB `FHIRString`, and `--enforce-must-support` / `enforce_must_support=True`.
  - Expanded precompiled schemas in `profiles.py` to `198` profiles (`3,579` core rules across R4 Core `49`, CA-Baseline `28`, CA Core `34`, UV IPS `33`, US Core `54`, plus `preferred_bindings` and `element_profiles`) and `441` Extension `StructureDefinition`s.
- **Transitive IG & Terminology Completeness**:
  - Added [`pkg_manager.py`](src/fhirlance/pkg_manager.py) and `fhirlance pkg install <id>#<version>` with recursive `package.json` dependency resolution into `~/.cache/fhirlance/packages/`.
  - Added [`vs_expansion.py`](src/fhirlance/vs_expansion.py) supporting `CodeSystem.supplements`, `ValueSet.compose.include.filter` (`exists`, `generalizes`, `child-of`, `not-in`, `is-a`, `descendent-of`, `is-not-a`, `=`, `in`, `regex`), `compose.exclude`, `expansion.contains`, and versioned canonicals (`url|version`), expanding compiled terminology to `3,061` CodeSystems and `7,139` ValueSets.
  - Added `--unknown-profile {ignore,warning,error}` CLI/API option.
- **Release Engineering & Documentation**:
  - Added tag-triggered GitHub Release workflow ([`.github/workflows/release.yml`](.github/workflows/release.yml)) with opt-in PyPI Trusted Publishing (`ENABLE_PYPI_PUBLISH=true`).
  - Documented [Differences from the Official HL7 Validator](docs/equivalence-and-testing.md#13-differences-from-the-official-hl7-validator), [FHIR Server Runtimes & Ingestion Architecture](docs/research-fhir-server-runtimes.md), split [CLI & Python API Reference](docs/usage.md) and [Architecture & Development Reference](docs/architecture.md), and added `NOTICE` and `CHANGELOG.md`.

### Fixed
- **Real-World Ontario Health IG Hardening (`ca.on.dhdr.r4.v4#4.0.0`, `ca.on.mi.r4#1.0.0-snapshot6`)**:
  - Normalized single `str` / `Path` inputs in `register_ig()` and IG loader functions rather than iterating string characters.
  - Supported `CanonicalResource` / `MetadataResource` supertypes and `<canonical-url>#<ElementPath>` context expressions in `extensions.py`.
  - Treated valid codes from `COMPLETE_CODE_SYSTEMS` extending a subset `extensible` ValueSet as non-blocking warnings (unless `--strict-extensible`).
  - Treated unexpanded empty `vs_spec` stubs as local pass-through under `--tx local`.
  - Added British imperial and yard UCUM bracketed units (`[foz_br]`, `[gal_br]`, `[pt_br]`, `[qt_br]`, `[syd_i]`, `[cyd_i]`) to offline UCUM validation.

### Changed
- **Relicensed** from `CC BY-NC 4.0` to **PolyForm Noncommercial License 1.0.0** (`PolyForm-Noncommercial-1.0.0`), Copyright (c) 2026 Brightwood Consulting Group Limited, with patent grant, software warranty disclaimers, and explicit noncommercial organization/personal/research terms.

---

## [0.2.0] - 2026-11-16

*(Tier 1 — Highest-Footprint Core Structures; development milestone merged on `main` ahead of the first tagged `v0.3.0` release.)*

### Added
- **First-Class Extension `StructureDefinition` Validation**: Added [`extension_spec.py`](src/fhirlance/extension_spec.py) and [`extensions.py`](src/fhirlance/extensions.py) to validate extension `context`, `value[x]` types and bindings, complex sub-extension slices, and `modifierExtension` rules.
- **Complete Slicing Semantics**: Added [`slicing_spec.py`](src/fhirlance/slicing_spec.py) and slicing evaluation in [`profile_engine.py`](src/fhirlance/profile_engine.py) for `value`, `pattern`, `type`, `profile`, and `exists` discriminators, slice `min`/`max`, `closed`/`openAtEnd`/`ordered` rules, and nested sub-slicing.
- **`Bundle` Reference Graph & Outer `Bundle` Validation**: Indexed `Bundle.entry[].fullUrl` and `contained[].id` to validate `Reference.type`, `targetProfile`, `aggregation`, and outer `Bundle` invariants (`bdl-1`–`bdl-12`).
- **Complex Datatype Element Bindings & Single-Pass Scan**: Extracted and enforced ValueSet bindings on complex datatypes via a single-pass coding and extension traversal in [`resource_validator.py`](src/fhirlance/resource_validator.py).

---

## [0.1.0] - 2026-11-14

*(Baseline — Initial public repository milestone.)*

### Added
- Compiled all **146 FHIR R4 resources** and **39 complex datatypes** into Pydantic v2 models backed by Rust `pydantic-core` (keeping `FHIRBaseModel` free of Python `@model_validator(mode="before")`, with lazy `_primitive` fallback in [`primitive_extensions.py`](src/fhirlance/primitive_extensions.py)).
- Compiled **183 IG profiles** across HL7 R4 Core, CA-Baseline, CA Core, UV IPS, and US Core, plus dynamic runtime `-ig` loading (`.tgz`, unpacked folders, `Bundle`s, `StructureDefinition`s).
- Added terminology engine ([`terminology.py`](src/fhirlance/terminology.py)) with offline UCUM/BCP-47/BCP-13/ISO-3166 grammars, `hl7.terminology.r4` complete CodeSystems, `--tx local|remote|off`, `--strict-extensible`, and L1/SQLite L2 caching.
- Added `fhirlance` CLI ([`cli.py`](src/fhirlance/cli.py)), multiprocessing dataset runner ([`dataset.py`](src/fhirlance/dataset.py)), and `OperationOutcome`, SARIF v2.1.0, JUnit XML, JSON, and text output formatters ([`formatters.py`](src/fhirlance/formatters.py)).
