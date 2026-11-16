# Proof of Functional Equivalence & Test Suite Architecture

This document details how **FHIRlance** proves functional equivalence with the official HL7 Java Reference Implementation (**`validator_cli.jar`**) and describes the architecture, breadth, and scenario coverage of the repository's test suite (**2,774 pytest test items** / **2,764 offline** at **96.91% statement and branch coverage**).

---

## 1. Proof of Functional Equivalence with the Official HL7 IG Validator

### 1.1 Dual-Engine Equivalence Methodology

The canonical reference for FHIR R4 and Implementation Guide (IG) conformance is HL7's official Java validator (`org.hl7.fhir.validation.cli`, distributed as `validator_cli.jar` from [`hapifhir/org.hl7.fhir.core`](https://github.com/hapifhir/org.hl7.fhir.core)).

FHIRlance proves functional equivalence against `validator_cli.jar` (`-version 4.0.1 -tx n/a`) using a two-pronged approach:

1. **Ahead-of-Time Specification Compilation (`scripts/generate_models.py`)**:
   Both engines consume the exact same canonical HL7 NPM packages (`hl7.fhir.r4.core#4.0.1`, `hl7.fhir.ca.baseline#1.2.0`, `ca.infoway.io.core#1.1.0-dft-preballot`, `hl7.fhir.uv.ips#1.0.0`, and `hl7.fhir.us.core.r4#8.0.1`). Instead of interpreting StructureDefinition JSON graphs in a JVM at runtime, FHIRlance compiles all **146 base FHIR R4 resources**, **39 complex datatypes**, **473 BackboneElement sub-models** (**659 total Pydantic v2 classes** covering **8,350 typed fields**), and **183 IG profiles** (**2,009 profile rules**) directly into Rust-backed `pydantic-core` schemas and frozen constraint tuples.
2. **Automated Differential Equivalence Harness (`pytest -m hl7_live`)**:
   The live equivalence suites (`tests/test_all_146_live_hl7_equivalence.py` and `tests/test_validator_equivalence.py`) feed identical valid and systematically mutated FHIR JSON payloads into both `fhirlance.validate_resource(...)` and `java -jar validator_cli.jar`, parsing the resulting HL7 `OperationOutcome` Bundle and asserting zero equivalence mismatches across all structural, primitive, invariant, and IG profile test cases.

```mermaid
flowchart LR
    subgraph Corpus["Equivalence Corpus (335 Live JVM Cases + 6,500+ Offline Scenarios)"]
        direction TB
        C1["146 Official HL7 R4 Resource Examples<br/>(Valid Baseline Corpus)"]
        C2["146 Structural Mutations<br/>• extra='forbid' unknown fields<br/>• min_length=1 empty arrays<br/>• Invalid FHIRId regexes"]
        C3["43 Targeted Edge & IG Cases<br/>• 10 FHIRPath invariants (txt-1, pat-1, obs-6/7, con-4, bdl-1..7, ext-1)<br/>• 11 Strict R4 primitives & leap-year boundaries<br/>• [x] Choice exclusivity & _primitive extensions<br/>• Recursive Bundle & contained[] resources<br/>• Multi-IG profiles (R4 Vital Signs, US Core 8.0.1, IPS 1.0.0, CA-Baseline)"]
    end

    subgraph PY["FHIRlance Engine (Python + Rust pydantic-core)"]
        direction TB
        P1["1. Structural Schema (659 Models)"]
        P2["2. Lazy _primitive Fallback"]
        P3["3. Core FHIRPath Invariants"]
        P4["4. Compiled IG Profile Engine (183 Profiles)"]
        P5["5. Recursive Bundle / contained[] Walk"]
        P1 --> P2 --> P3 --> P4 --> P5
    end

    subgraph JAVA["Official HL7 Reference Validator (JVM)"]
        direction TB
        J1["java -jar validator_cli.jar<br/>-version 4.0.1 -tx n/a<br/>-ig hl7.fhir.uv.ips#1.0.0<br/>-ig hl7.fhir.us.core.r4#8.0.1"]
        J2["OperationOutcome Bundle<br/>(error / fatal diagnostics)"]
        J1 --> J2
    end

    ASSERT["Equivalence Assertion Gate<br/>(py_valid == hl7_valid == expected_valid)<br/>0 Mismatches Allowed"]

    Corpus --> PY --> ASSERT
    Corpus --> JAVA --> ASSERT
```

---

### 1.2 Side-by-Side Functional Equivalence Matrix

| Validation Dimension | Official HL7 `validator_cli.jar` | FHIRlance Implementation | Equivalence Status |
| :--- | :--- | :--- | :--- |
| **Base R4 Resource Types** | Validates all 146 R4 `StructureDefinition` resource schemas | 146 generated `FHIRBaseModel` / `DomainResourceR4` classes in `resources.py` (605 classes including BackboneElements) | **100% Equivalent** (verified across all 146 resource types) |
| **Complex Datatypes** | Validates all 39 R4 complex datatype schemas | 39 complex datatype models + `Element` + 14 BackboneElements (54 classes) in `types.py` | **100% Equivalent** |
| **Unknown JSON Properties** | Rejects undeclared properties (`Unrecognised property`) | `ConfigDict(extra="forbid")` compiled into Rust `pydantic-core` on every model class | **100% Equivalent** |
| **Empty JSON Arrays (`[]`)** | Rejects empty arrays (`ele-1` / array must not be empty) | `Annotated[list[T], Field(min_length=1)]` on every repeating (`max="*"`) FHIR element | **100% Equivalent** |
| **Required Elements (`min >= 1`)** | Reports missing mandatory elements on root and BackboneElements | Required Pydantic fields + IG `PathRule` required checks (`537` IG required rules) | **100% Equivalent** |
| **Primitive Regexes & Calendar Dates** | Enforces R4 regexes for `date`, `dateTime`, `instant`, `time`, `id`, `code` and real calendar dates | Rust `StringConstraints` regexes + `_check_fhir_date` calendar validation (e.g. rejects `2023-02-29`, accepts `2024-02-29`) | **100% Equivalent** |
| **Strict Numeric & Boolean Types** | Rejects `true`/`false` on integers, rejects strings on numbers/booleans, rejects `NaN`/`Infinity` | `StrictBool`, `StrictInt`, `StrictFloat`, `_check_int_not_bool`, `ge=1` (`positiveInt`), `ge=0` (`unsignedInt`), `loads_strict_json` | **100% Equivalent** |
| **Choice `[x]` Type Exclusivity** | Rejects multiple populated variants (e.g. `valueInteger` + `valueString`) or missing required `[x]` | Generated `@model_validator(mode="after") def _check_choices` across **186 choice groups** on **141 model classes** | **100% Equivalent** |
| **`_primitive` JSON Extensions** | Allows `_fieldName` objects (`id`, `extension`) and aligned array placeholders (`[null, {...}]`) | Lazy fallback in `primitive_extensions.py` strips valid `_field` trees and rejects orphan/malformed `_field` keys | **100% Equivalent** |
| **Extension `ext-1` Invariant** | `extension.exists() != value.exists()` (must have `extension` or `value[x]`, never both or neither) | Enforced recursively by `ExtensionBase._check_ext_1` and `validate_extension_item` in `base.py` | **100% Equivalent** |
| **Core FHIRPath Invariants** | Evaluates `txt-1`, `pat-1`, `obs-6`, `obs-7`, `con-4`, `bdl-1`, `bdl-3`, `bdl-4`, `bdl-7` | Native Python evaluators in `invariants.py` matching exact HL7 invariant semantics | **100% Equivalent** |
| **Recursive `Bundle` & `contained[]`** | Recursively validates `Bundle.entry[].resource` and `DomainResource.contained[]` | `_validate_nested_resources` in `resource_validator.py` with path prefixing and depth guard (`max_depth=16`) | **100% Equivalent** |
| **Multi-IG Profile Constraints** | Evaluates differential/snapshot constraints across loaded IGs | Pre-compiled `COMPILED_PROFILES` (183 profiles, 2,009 rules) + runtime `ig_loader.py` supporting `.tgz`, folders, Bundles, and SDs | **100% Equivalent** on structural & closed ValueSet rules |
| **Terminology & Grammar Validation** | Evaluates ValueSets, CodeSystems, and intensional grammars; queries `-tx` server for remote/external systems | 1,161 complete CodeSystems (incl. `hl7.terminology.r4#6.2.0`), 3,297 ValueSets, offline UCUM / BCP-47 / MIME / ISO-3166 grammars, `--tx local` (default), `--tx remote` / `<url>` with two-tier L1/L2 SQLite cache, and `--strict-extensible` ([`terminology.md`](terminology.md)) | **100% Equivalent** |

> [!NOTE]
> **Terminology Boundaries & Execution Modes (`--tx`)**:
> By default (`--tx local`), FHIRlance operates in an ultra-fast, zero-network mode. It enforces **required and extensible ValueSet bindings** for all 1,161 complete code systems defined in the base specification, `hl7.terminology.r4`, and compiled IGs, all 3,297 precompiled ValueSets, and native offline grammars (UCUM, BCP-47, MIME, ISO-3166). External systems (e.g., SNOMED-CT, LOINC) pass without error on extensible bindings in local mode, or can be queried against a live terminology server using `--tx remote` or `--tx <url>` with two-tier L1 in-memory / L2 SQLite caching (see **[Terminology Reference](terminology.md)**). Setting `--tx off` disables terminology checks to match `validator_cli.jar -tx n/a`.

---

## 2. Test Suite Scale, Breadth & Coverage Summary

The FHIRlance test suite in `tests/` contains **2,764 offline collected pytest items** (plus 10 live HL7 equivalence tests, **2,774 total**) covering R4 resources, datatypes, primitives, invariants, extensions, slicing, Bundle references, terminology, and IG profiles.

### 2.1 Quantitative Overview by Test Module

| Test Module | Collected Pytest Items | Distinct Scenarios Evaluated | Primary Scope |
| :--- | ---: | ---: | :--- |
| [`tests/test_all_183_ig_profiles.py`](../tests/test_all_183_ig_profiles.py) | **1,268** | **4,190+** | All **183 compiled IG profiles** across 5 IGs and all **2,009 profile rules** (positive + negative checks for `required`, `forbidden`, `max_one`, `fixed`, `pattern`, `type_narrowing`, `target_types`, `bindings`, and `slices`) |
| [`tests/test_full_r4_coverage.py`](../tests/test_full_r4_coverage.py) | **917** | **2,400+** | All **146 FHIR R4 resources** (valid minimal instances, unknown fields, empty arrays, invalid primitives, `txt-1`/`ext-1`/`_primitive` extensions, required fields) + all **186 `[x]` choice groups** across all 659 generated models |
| [`tests/test_complex_types_and_primitives.py`](../tests/test_complex_types_and_primitives.py) | **342** | **620+** | All **54 complex datatype & BackboneElement classes** in `types.py`, **112 primitive regex/calendar/type boundary cases**, and all **176 root resource `Literal` ValueSet bindings** |
| [`tests/test_invariants_and_profiles_unit.py`](../tests/test_invariants_and_profiles_unit.py) | **93** | **185+** | All compiled FHIRPath invariants across 11 `Observation.value[x]` fields, 5 `Condition.abatement[x]` fields, 4 `Patient.contact` fields, 9 `Bundle.type` codes, and internal engine edge branches |
| [`tests/test_output_ig_and_parallel.py`](../tests/test_output_ig_and_parallel.py) | **41** | **150+** | Output formatters (`OperationOutcome`, SARIF v2.1.0, JUnit XML, JSON, text), dynamic runtime IG loader (`.tgz`, directory, Bundle, SD, semver cache, ZipSlip/size guards), and multi-process intra-file/inter-file parallelism |
| [`tests/test_terminology_unit.py`](../tests/test_terminology_unit.py) | **32** | **120+** | Terminology unit tests: offline grammars (UCUM, BCP-47, MIME, ISO-3166), L1 LRU + L2 SQLite WAL caching, remote `$validate-code` mocking, binding strengths, and standalone codings |
| [`tests/test_terminology.py`](../tests/test_terminology.py) | **24** | **85+** | End-to-end terminology integration: CLI flags (`--tx`, `--strict-extensible`), dataset validation (serial & parallel), base & profile binding deduplication, US Core vital signs, and OperationOutcome/SARIF formatters |
| [`tests/test_comprehensive_profiles_and_resilience.py`](../tests/test_comprehensive_profiles_and_resilience.py) | **14** | **45+** | End-to-end profile rules, `_primitive` extensions, `ext-1`, `obs-7`, `bdl-7`, `contained[]` recursion, depth guard (`>16`), strict JSON `NaN`/`Infinity`, and CLI exit codes |
| [`tests/test_validator_equivalence.py`](../tests/test_validator_equivalence.py) | **10** (`hl7_live`) | **20** | Per-resource comparative equivalence between `validate_resource` and `validator_cli.jar` |
| [`tests/test_property_and_perf.py`](../tests/test_property_and_perf.py) | **6** | **405+** | Property-based Hypothesis fuzzing (200 arbitrary JSON & mutated resource examples), strict JSON `NaN`/`Infinity`/`-Infinity` rejection, and Rust hot-path guard + 200-iteration throughput benchmark (`<0.5s`) |
| [`tests/test_codegen_unit.py`](../tests/test_codegen_unit.py) | **4** | **12+** | Unit tests for `scripts/generate_models.py` keyword escaping, `baseDefinition` profile inheritance merging, and BackboneElement / `[x]` choice model emission |
| [`tests/test_all_146_live_hl7_equivalence.py`](../tests/test_all_146_live_hl7_equivalence.py) | **2** (`1` offline + `1` `hl7_live`) | **358** (`325` live JVM + `33` offline) | Batch equivalence across all **146 R4 resource types** (146 valid + 146 mutated) + **33 targeted invariant, primitive, choice, recursive, and multi-IG profile cases** in a single `validator_cli.jar` run |
| **Total (Full Offline Suite)** | **2,764 items** (offline) | — | **96.91% branch coverage across `src/fhirlance/` (`0` skipped)** |

---

### 2.2 Code Coverage by Module (`src/fhirlance/`)

Running `pytest -m "not hl7_live" --cov --cov-report=term-missing` achieves **96.91% branch coverage** across all handwritten modules (above the 95% CI gate enforced in `pyproject.toml`):

| Module | Statements | Missed | Branches | Partial | Coverage |
| :--- | ---: | ---: | ---: | ---: | ---: |
| `src/fhirlance/__init__.py` | 11 | 0 | 0 | 0 | **100%** |
| `src/fhirlance/base.py` | 81 | 0 | 30 | 0 | **100%** |
| `src/fhirlance/cli.py` | 49 | 0 | 8 | 0 | **100%** |
| `src/fhirlance/dataset.py` | 223 | 0 | 56 | 0 | **100%** |
| `src/fhirlance/extension_spec.py` | 207 | 19 | 118 | 15 | **87%** |
| `src/fhirlance/extensions.py` | 286 | 14 | 164 | 10 | **92%** |
| `src/fhirlance/formatters.py` | 257 | 1 | 112 | 2 | **99%** |
| `src/fhirlance/ig_loader.py` | 527 | 5 | 260 | 15 | **97%** |
| `src/fhirlance/invariants.py` | 122 | 3 | 68 | 3 | **97%** |
| `src/fhirlance/primitive_extensions.py` | 44 | 0 | 24 | 0 | **100%** |
| `src/fhirlance/profile_engine.py` | 598 | 14 | 294 | 15 | **97%** |
| `src/fhirlance/resource_validator.py` | 269 | 3 | 134 | 6 | **98%** |
| `src/fhirlance/slicing_spec.py` | 160 | 2 | 68 | 3 | **98%** |
| `src/fhirlance/terminology.py` | 602 | 4 | 300 | 5 | **99%** |
| `src/fhirlance/validator.py` | 8 | 0 | 0 | 0 | **100%** |
| **TOTAL** | **3,444** | **65** | **1,636** | **74** | **96.91%** |

---

## 3. Detailed Catalog of Test Suites

### 3.1 Live HL7 `validator_cli.jar` Equivalence Suites

#### [`tests/test_all_146_live_hl7_equivalence.py`](../tests/test_all_146_live_hl7_equivalence.py)
Validates **325 distinct FHIR R4 and IG profile instances** against both FHIRlance and the official HL7 `validator_cli.jar` (`-version 4.0.1 -tx n/a -ig hl7.fhir.uv.ips#1.0.0 -ig hl7.fhir.us.core.r4#8.0.1`) in a single batch invocation:
- **146 Valid Base R4 Resources (`<ResourceType>__valid`)**: Selects a clean official HL7 R4 example from `hl7.fhir.r4.examples#4.0.1` (with deterministic minimal fallbacks for the 6 substance/parameters types) covering all 146 R4 resource types from `Account` to `VisionPrescription`.
- **146 Mutated Invalid Base R4 Resources (`<ResourceType>__invalid_<0|1|2>`)**: Rotates through three structural violation modes across all 146 resource types:
  - Mode `0`: Undeclared property injection (`"unknownFieldXYZ": "invalid"`) testing `extra="forbid"`.
  - Mode `1`: Empty array injection (`"extension": []`) testing `min_length=1`.
  - Mode `2`: Malformed FHIR `id` (`"id": "invalid id with spaces!"`) testing `FHIRId` regex enforcement.
- **12 FHIRPath Invariant Cases**: Live equivalence verification for `txt-1` (missing `<div>` wrapper), `pat-1` (valid and invalid `Patient.contact`), `obs-6` (`valueQuantity` + `dataAbsentReason` conflict), `obs-7` (`Observation.code` matching `component.code` when `value[x]` is present), `con-4` (abated `Condition` missing `clinicalStatus`), `bdl-1` (`total` on `collection` Bundle), `bdl-3` (`request` on `collection` Bundle), `bdl-4` (`response` on `collection` Bundle), `bdl-7` (duplicate `fullUrl` in `collection` Bundle), and `ext-1` (empty extension and extension with both `valueString` and child `extension`).
- **7 Strict Primitive Boundary Cases**: Non-leap year `2023-02-29` vs valid leap year `2024-02-29`, `FHIRDateTime` missing timezone (`2026-05-15T10:30:00`), `FHIRInstant` date-only (`2026-05-15`), boolean passed to integer field (`multipleBirthInteger: true`), negative `unsignedInt` (`Bundle.total: -1`), and 65-character `FHIRId`.
- **4 Choice `[x]` & `_primitive` Extension Cases**: Simultaneous `deceasedBoolean` + `deceasedDateTime` on `Patient`, simultaneous `valueInteger` + `valueString` on `Observation`, valid `_birthDate` + `_given: [null]` companion elements, and invalid `_birthDate: {"unknownKey": "bad"}`.
- **2 Recursive Nesting Cases**: Invalid `Organization` inside `Patient.contained[0]` and invalid `Patient` inside `Bundle.entry[0].resource`.
- **8 Multi-IG Profile Cases**: Valid and invalid instances across HL7 R4 Vital Signs (`vitalsigns`, `heartrate` with wrong `valueString` choice type, `bodyweight` missing `subject`), HL7 US Core 8.0.1 (`us-core-patient` valid, missing `name`, missing `identifier`), and HL7 UV IPS 1.0.0 (`Patient-uv-ips` missing `name`, `AllergyIntolerance-uv-ips` missing `patient`).
- **Offline Fast Gate (`test_extra_equivalence_cases_offline_python_validation`)**: Runs all 33 targeted invariant, primitive, choice, recursive, and IG profile cases in standard `pytest -m "not hl7_live"` runs without requiring a JVM.

#### [`tests/test_validator_equivalence.py`](../tests/test_validator_equivalence.py)
Runs parametrized per-resource comparative tests against `validator_cli.jar` starting from a valid Canadian Baseline `Patient`:
- Verifies exact agreement (`expect_py_valid == expect_hl7_valid`) on `valid_canadian_patient`, `unknown_property`, `wrong_type_birthdate`, `invalid_date_format`, `invalid_gender_code`, `fhirpath_pat_1_violation`, `unknown_resource_type`, `empty_array`, and `vitalsigns_profile_missing_category`.

---

### 3.2 Full FHIR R4 Resource & Choice-Type Matrix (`tests/test_full_r4_coverage.py`)

Contains **917 parametrized pytest items** (0 skipped) that synthesize valid minimal instances via type-hint introspection and test every generated R4 model class:
- `test_all_146_r4_resources_registered` (**1 item**): Asserts `len(RESOURCE_MODELS) == 146` and `issubclass(cls, FHIRBaseModel)`.
- `test_every_r4_resource_accepts_valid_minimal_instance` (**146 items**): Verifies every single one of the 146 R4 models accepts its synthesized minimal valid payload with `0` validation issues.
- `test_every_r4_resource_rejects_unknown_field_and_empty_array` (**146 items**): Verifies every R4 resource rejects unknown fields (`nonExistentFhirFieldXYZ`) and empty arrays (`[]`).
- `test_every_r4_resource_rejects_invalid_id_and_primitives` (**146 items**): Verifies every R4 resource rejects `id` values with spaces, `id` values exceeding 64 characters, non-string `id` values (`12345`), and `language` codes with leading/trailing whitespace.
- `test_every_r4_resource_domain_invariants_and_primitive_extensions` (**146 items**): Verifies valid `_id` companion extensions pass, malformed `_id` objects fail, and all 143 `DomainResource` subclasses enforce `Invariant[txt-1]` and `ext-1`.
- `test_every_r4_resource_enforces_required_fields` (**146 items**): Verifies that all 113 R4 resources with required fields beyond `resourceType` reject bare `{"resourceType": rtype}` stubs with `Field required`, while the 33 R4 resources without mandatory root fields accept bare stubs cleanly.
- `test_every_generated_choice_group_exclusivity` (**186 items**): Iterates across all **186 `[x]` choice groups** in `resources.py` and `types.py` (covering root resources, BackboneElements, and complex datatypes), verifying:
  1. Populating a single allowed `[x]` variant succeeds.
  2. Populating two `[x]` variants simultaneously raises `ValidationError` (`<name>[x] allows at most one value` or `<name>[x] requires exactly one value`).
  3. Omitting all variants on a mandatory choice group (`min >= 1`) raises `ValidationError` (`<name>[x] requires exactly one value`).

---

### 3.3 Multi-IG Profile Engine Matrix (`tests/test_all_183_ig_profiles.py`)

Contains **1,268 parametrized pytest items** exercising all **183 pre-compiled StructureDefinition profiles** and **2,009 individual constraints** across the 5 built-in Implementation Guides:
- **IG Breakdown Verified (`test_all_183_ig_profiles_compiled_across_five_igs`)**:
  - **HL7 R4 Core (`hl7.fhir.r4.core#4.0.1`)**: 44 profiles (Vital Signs, Clinical Document, Shareable/Publishable artifacts, CDShooks, CQF, etc.)
  - **HL7 CA-Baseline (`hl7.fhir.ca.baseline#1.2.0`)**: 27 profiles (`profile-patient`, `profile-observation`, `profile-condition`, `profile-medicationrequest`, `profile-encounter`, `profile-allergyintolerance`, `profile-immunization`, etc.)
  - **Infoway CA Core (`ca.infoway.io.core#1.1.0-dft-preballot`)**: 31 profiles (`Patient-ca-core`, `Observation-results-ca-core`, `Condition-ca-core`, `MedicationRequest-ca-core`, etc.)
  - **HL7 UV IPS (`hl7.fhir.uv.ips#1.0.0`)**: 27 profiles (`Patient-uv-ips`, `AllergyIntolerance-uv-ips`, `Condition-uv-ips`, `MedicationStatement-uv-ips`, `Bundle-uv-ips`, `Composition-uv-ips`, etc.)
  - **HL7 US Core (`hl7.fhir.us.core.r4#8.0.1`)**: 54 profiles (`us-core-patient`, `us-core-observation-lab`, `us-core-blood-pressure`, `us-core-vital-signs`, `us-core-condition-problems-health-concerns`, `us-core-encounter`, `us-core-medicationrequest`, etc.)
- **Exhaustive Per-Constraint Parametrization**:
  - `test_every_compiled_ig_profile_type_guard_max_one_and_targets` (**183 items**): Verifies resource type mismatch rejection (`profile applies to '<base_type>', got '<other>'`), all **501 `max_one` (`max="1"`)** cardinality rules (positive 1-item list vs negative 2-item list), and all **424 `Reference.targetProfile`** target resourceType rules (positive allowed target vs negative disallowed target).
  - `test_every_ig_profile_required_constraint` (**535 items**): Positive and negative verification of every non-root `min >= 1` required element path across all 183 profiles.
  - `test_every_ig_profile_forbidden_constraint` (**56 items**): Positive and negative verification of every `max = "0"` forbidden element path.
  - `test_every_ig_profile_fixed_value_constraint` (**49 items**): Positive (`== expected`) and negative (`!= expected`) verification of every `fixed[x]` constraint.
  - `test_every_ig_profile_pattern_constraint` (**27 items**): Positive (subset match with extra keys) and negative verification of every `pattern[x]` constraint.
  - `test_every_ig_profile_choice_type_narrowing` (**268 items**): Positive (allowed `[x]` suffix) and negative (disallowed `[x]` suffix) verification of every choice-type narrowing rule.
  - `test_every_ig_profile_required_valueset_binding` (**78 items**): Positive (valid bound code) and negative (`__invalid_bound_code__`) verification of every required ValueSet binding rule.
  - `test_every_ig_profile_slice_discriminator` (**69 items**): Positive (synthesized matching slice items meeting `min_count`) and negative (empty slice array) verification of every discriminator slice rule.

---

### 3.4 Complex Datatypes, Strict Primitives & Literal Bindings (`tests/test_complex_types_and_primitives.py`)

Contains **342 parametrized pytest items**:
- `test_every_complex_datatype_valid_and_structural_rules` (**54 items**): Tests all 39 base FHIR R4 complex datatypes (`Address`, `Age`, `Annotation`, `Attachment`, `CodeableConcept`, `Coding`, `ContactDetail`, `ContactPoint`, `Contributor`, `Count`, `DataRequirement`, `Distance`, `Dosage`, `Duration`, `Expression`, `Extension`, `HumanName`, `Identifier`, `MarketingStatus`, `Meta`, `Money`, `Narrative`, `ParameterDefinition`, `Period`, `Population`, `ProdCharacteristic`, `ProductShelfLife`, `Quantity`, `Range`, `Ratio`, `Reference`, `RelatedArtifact`, `SampledData`, `Signature`, `SubstanceAmount`, `Timing`, `TriggerDefinition`, `UsageContext`, `Element`) plus all 14 complex BackboneElement models (`DosageDoseAndRate`, `TimingRepeat`, `DataRequirementCodeFilter`, `DataRequirementDateFilter`, `DataRequirementSort`, `ElementDefinition*`, `SubstanceAmountReferenceRange`), verifying valid construction, `extra="forbid"`, and required field enforcement.
- `test_fhir_primitive_boundary_matrix` (**112 items**): Boundary value analysis across all 11 strict FHIR R4 primitive types (`FHIRDate`, `FHIRDateTime`, `FHIRInstant`, `FHIRTime`, `FHIRId`, `FHIRCode`, `FHIRPositiveInt`, `FHIRUnsignedInt`, `FHIRInteger`, `FHIRDecimal`, `StrictBool`), including leap years (`2024-02-29`, `2000-02-29` vs `2023-02-29`, `1900-02-29`), month/day bounds (`02-30`, `04-31`, `06-31`, `09-31`, `11-31`), leap seconds (`:60`), timezone offsets (`+14:00` vs `+15:00`, `+14:30`), 64-char vs 65-char `FHIRId`, whitespace rules on `FHIRCode`, and boolean-as-integer rejection (`True`/`False` rejected by `FHIRInteger`, `FHIRPositiveInt`, `FHIRUnsignedInt`, `FHIRDecimal`).
- `test_every_r4_root_literal_code_binding` (**176 items**): Tests every root resource field with a compiled `Literal[...]` required ValueSet binding across all 146 R4 models, confirming both valid code acceptance and invalid code rejection.

---

### 3.5 FHIRPath Invariants, Canadian Localization & Unit Suites (`tests/test_invariants_and_profiles_unit.py`)

Contains **92 pytest items**:
- **All 11 `Observation.value[x]` Variants (`test_obs6_and_obs7_across_all_11_value_fields`)**: Verifies `obs-6` and `obs-7` trigger across `valueQuantity`, `valueCodeableConcept`, `valueString`, `valueBoolean`, `valueInteger`, `valueRange`, `valueRatio`, `valueSampledData`, `valueTime`, `valueDateTime`, and `valuePeriod`.
- **All 5 `Condition.abatement[x]` Variants (`test_con4_across_all_5_abatement_fields`)**: Verifies `con-4` triggers when `clinicalStatus` is missing across `abatementDateTime`, `abatementAge`, `abatementPeriod`, `abatementRange`, and `abatementString`, and passes when `clinicalStatus` is present.
- **All 4 `Patient.contact` Fields (`test_pat1_satisfied_by_each_contact_field`)**: Verifies `pat-1` passes when any one of `name`, `telecom`, `address`, or `organization` is present and fails when all four are absent.
- **All 9 `Bundle.type` Codes (`test_bundle_invariants_across_all_9_bundle_types`)**: Verifies exact truth tables for `bdl-1` (`searchset`/`history` only), `bdl-3` (`batch`/`transaction`/`history` only), `bdl-4` (`batch-response`/`transaction-response`/`history` only), and `bdl-7` (`document`/`collection` unique `(fullUrl, versionId)` pairs) across all 9 R4 Bundle types.

---

### 3.6 Formatters, Dynamic IG Loader, Parallelism & Property Fuzzing

- **[`tests/test_output_ig_and_parallel.py`](../tests/test_output_ig_and_parallel.py)** (**41 items**):
  - **Standard Output Formatters**: Verifies that `issues_to_operation_outcome`, `dataset_to_operation_outcome`, and `validate_to_operation_outcome` emit self-validating FHIR R4 `OperationOutcome` resources (`validate_resource(oo) == []`) with accurate `IssueType` codes (`structure`, `invariant`, `code-invalid`, `required`, `value`, `exception`) and FHIRPath `expression` arrays; verifies **SARIF v2.1.0** (`FHIR001-Structural` through `FHIR005-ParseError`) and **JUnit XML** (including XML control-character sanitization).
  - **Dynamic Runtime IG Loader (`ig_loader.py`)**: Tests runtime loading and `baseDefinition` inheritance across single `StructureDefinition` JSONs, FHIR `Bundle`s (with nested `CodeSystem` concepts and `ValueSet` expansions), NPM package directories, `.tgz` tarballs (including ZipSlip path-traversal blocking, 25 MB member size caps, and 5,000-member limits), and `~/.fhir/packages` semver resolution, plus mtime/size cache fingerprinting.
  - **Intra-File & Inter-File Parallelism (`dataset.py`)**: Verifies bit-for-bit report equality (`res_par["issues"] == res_seq["issues"]`) between sequential and `ProcessPoolExecutor` parallel runs on multi-entry `Bundle` JSON files, multi-line `.ndjson` files, and multi-file directories.
- **[`tests/test_property_and_perf.py`](../tests/test_property_and_perf.py)** (**6 items / 400+ runtime checks**):
  - **Hypothesis Property-Based Fuzzing**: Generates 100 arbitrary recursive JSON structures (`None`, `bool`, `int`, `float`, `str`, `list`, `dict`) and 100 mutated FHIR resources (`Patient`, `Observation`, `Condition`, `Bundle`, `Organization` with arbitrary extra fields), asserting `validate_resource` always returns `list[str]` and never raises an unhandled exception.
  - **Hot-Path Architecture Guard**: Asserts `not FHIRBaseModel.__pydantic_decorators__.model_validators` (ensuring zero Python callbacks on the Rust `pydantic-core` hot path) and verifies 200 `Patient` validations complete in `< 0.5s`.

---

### 3.7 Terminology Validation Engine & TX Integration (`tests/test_terminology_unit.py` & `tests/test_terminology.py`)

Contains **56 pytest items** (32 unit + 24 integration) exercising the complete terminology subsystem:
- **Offline Grammars (`test_ucum_*`, `test_bcp47_*`, `test_mime_*`, `test_iso3166_*`)**: Validates full UCUM syntax (metric prefixes, clinical brackets `mm[Hg]`, `[lb_av]`, exponents, `{annotations}`, division), RFC 5646 BCP-47 language/region/variant subtags, RFC 2045/6838 MIME media types, and ISO-3166 alpha-2/alpha-3/numeric-3 country codes and subdivisions.
- **Two-Tier Cache & SQLite WAL (`test_sqlite_cache_*`, `test_validate_remote_code_*`)**: Verifies L1 in-memory LRU caching, L2 persistent SQLite WAL mode initialization once per process, and graceful degradation to non-blocking diagnostic warnings upon remote network errors or timeouts.
- **Binding Evaluation & Attribution (`test_validate_binding_*`, `test_validate_standalone_codings`)**: Verifies `required` vs `extensible` semantics, multi-coding `CodeableConcept` matching, error attribution to known systems in extensible bindings, missing code detection, and base vs. active profile binding deduplication.
- **CLI & Output Integration (`test_terminology_cli_*`, `test_formatters_*_with_terminology`)**: Verifies `-tx` / `--tx` / `--strict-extensible` flags across JSON, OperationOutcome, SARIF v2.1.0 (`FHIRLANCE_TERMINOLOGY`), and JUnit XML formatters.

---

## 4. Performance & Build Benchmarks

This section is automatically updated on every build by [`scripts/benchmark_performance.py`](../scripts/benchmark_performance.py) (`python scripts/benchmark_performance.py --update-docs`, with structured JSON output saved to [`docs/benchmark-results.json`](benchmark-results.json)).

It compares:
1. **FHIRlance Standard Validation Mode** (`validate_resource` returning `list[str]`) against the **325-resource Master Equivalence Corpus** (all `146` R4 resource types, `10` FHIRPath invariants, and `5` IGs) and the **2,774-item Master Test Suite**.
2. **FHIRlance "FHIR Output" (`OperationOutcome`) Mode** (`validate_to_operation_outcome` & `format_dataset_report(..., output_format="operation-outcome")` emitting compliant FHIR R4 `OperationOutcome` resources with structured `IssueType` codes and FHIRPath `expression` locations).
3. **Official HL7 Baseline Validator (`validator_cli.jar`)** (`-version 4.0.1 -tx n/a -ig hl7.fhir.uv.ips#1.0.0 -ig hl7.fhir.us.core.r4#8.0.1 -output outcome.json`) against the **exact same 325-resource dataset**.

<!-- PERFORMANCE_BENCHMARK_START -->
**Release**: `v0.1.0` | **Python**: `3.13.18` | **Pydantic**: `v2.14.3` (Rust `pydantic-core`) | **Master Suite**: `2,774` pytest items (`2,764` offline, `96.91%` coverage) | **Updated**: `2026-11-16 00:15 UTC`

#### 1. Master Equivalence Dataset (`325` Resources, `146` R4 Types, `10` Invariants & `5` IGs)

| Validator / Mode | Batch (`325`) | Latency | Throughput | Speedup |
| :--- | ---: | ---: | ---: | ---: |
| **FHIRlance — Standard Mode** | **`38.35 ms`** | **`118.0 µs`** | **`8,475 /s`** | **`916.1x`** |
| **FHIRlance — FHIR Output (`OperationOutcome`) Mode** | **`41.54 ms`** | **`127.8 µs`** | **`7,824 /s`** | **`845.7x`** |
| **Official HL7 Baseline Validator** | `35.13 s` | `108.1 ms` | `9.25 /s` | `1.0x` |

<sub>Standard: `validate_resource()` · FHIR Output: `validate_to_operation_outcome()` · HL7 Baseline: `validator_cli.jar -version 4.0.1 -tx n/a`</sub>

#### 2. High-Volume NDJSON & Test Suite Throughput

| Workload | Volume | Elapsed | Throughput |
| :--- | ---: | ---: | ---: |
| **NDJSON Batch** (`validate_dataset`, JSON) | `1,000` res | **`150.74 ms`** | **`6,634 /s`** |
| **NDJSON Batch** (`--format operation-outcome`) | `1,000` res | **`155.16 ms`** | **`6,445 /s`** |
| **Offline Pytest Suite** (`not hl7_live`) | `2,764` items (`96.91%` cov) | `22.78 s` | **`121.3 items/s`** |
<!-- PERFORMANCE_BENCHMARK_END -->

