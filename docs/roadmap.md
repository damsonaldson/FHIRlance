# FHIRlance Roadmap: Footprint-Prioritized Validation & HAPI / Smile CDR Integration

> [!IMPORTANT]
> **Baseline Advantage**: FHIRlance already validates all 146 FHIR R4 resource types, 39 complex datatypes, 183 IG profiles, Extension `StructureDefinition`s, full slicing, `Bundle` reference graphs, and 1,161 CodeSystems / 3,297 ValueSets at **~118 µs/resource (~8,500 res/s per core)** in-process (`pydantic-core` Rust hot-path) vs. **35.13 s (`108.1 ms/resource`)** for `validator_cli.jar` (**916.1x speedup**).
> **Architecture Decision (Python-First)**: At ~0.12 ms/resource, validation is already faster than downstream FHIR server DB writes and search indexing. Rather than taking on a two-language Rust rewrite (`PyO3`/C-ABI) for academic microsecond gains, FHIRlance stays **Python-first** (`pydantic-core` + pure Python), focusing engineering effort on **conformance completeness** (Tier 2) and **server/sidecar integration** (Tier 3).
> **Prioritization Principle**: Features are ordered by **real-world FHIR community footprint** — validating the **most widely used structures first** (core clinical resources, extensions, slicing, `Bundle` references, and common IG constraints) and **less used / long-tail structures last** (`Questionnaire` `que-*`, `CapabilityStatement`, `MedicinalProduct*`, `ConceptMap`, `R4B`/`R5`).

```mermaid
flowchart LR
    T1["Tier 1 (Done)<br/>Extensions, Full Slicing,<br/>Bundle Refs & Datatype Bindings"] --> T2["Tier 2 (Next #1)<br/>AOT + Combinator FHIRPath,<br/>Element Bounds & Transitive IGs"]
    T2 --> T3["Tier 3 (Planned)<br/>fhirlance serve UDS Daemon,<br/>HAPI/Smile Interceptor & mmap"]
    T3 --> T4["Tier 4 (Long-Term)<br/>Niche Resources, R4B/R5"]
```

---

## Summary Milestone Matrix (Ordered by FHIR Community Footprint)

| Tier / Phase | Target | Status | Milestone (Most-Used Structures First) | Primary Surface |
| :--- | :---: | :---: | :--- | :--- |
| **Baseline (`v0.1.0`)** | `v0.1.0` | **Done** | 146 R4 Resources, 39 Datatypes, 183 Profiles, Dynamic `-ig`, Local/SQLite TX (`hl7.terminology.r4` + 5 IGs), `OperationOutcome`/SARIF/JUnit | [`resources.py`](../src/fhirlance/resources.py), [`profile_engine.py`](../src/fhirlance/profile_engine.py), [`terminology.py`](../src/fhirlance/terminology.py) |
| **Tier 1 (`v0.2.0`)** | `v0.2.0` | **Done** | **Highest-Footprint Structures**: Extension `StructureDefinition`s, Full Slicing (`type`/`profile`/`exists`, slice `max`, `closed`/`ordered`, nested sub-slicing), `Bundle` Reference/`targetProfile`/`aggregation` Graph & Outer `Bundle` Check, Complex Datatype Bindings (`Identifier.type`, `ContactPoint`, `Address`), Single-Pass Scan | [`extensions.py`](../src/fhirlance/extensions.py), [`slicing_spec.py`](../src/fhirlance/slicing_spec.py), [`profile_engine.py`](../src/fhirlance/profile_engine.py), [`resource_validator.py`](../src/fhirlance/resource_validator.py) |
| **Tier 2 (`v0.3.0`)** | `v0.3.0` | **Next (#1)** | **High-Footprint Conformance**: AOT Python + Zero-`exec` Combinator FHIRPath (`ElementDefinition.constraint`), `maxLength`/`minValue`/`maxValue`/`type.profile`, Transitive `package.json` IG Dependencies, Versioned Canonicals (`url\|version`), `--best-practice` (`dom-6`), `--enforce-must-support`, `unknown-profile` | [`invariants.py`](../src/fhirlance/invariants.py), [`ig_loader.py`](../src/fhirlance/ig_loader.py), [`terminology.py`](../src/fhirlance/terminology.py) |
| **Tier 3 (`v0.4.0`)** | `v0.4.0` | **Planned** | **Server & Enterprise Scale**: `fhirlance serve` UDS/HTTP `$validate` Sidecar, **HAPI FHIR / Smile CDR Raw-Byte Interceptor**, Envoy/NGINX Edge Filter, `mmap` Multi-GB NDJSON Streaming | Unix Domain Socket (`/run/fhirlance.sock`), Java HAPI Interceptor |
| **Tier 4 (`v1.0.0`)** | `v1.0.0` | **Long-Term** | **Long-Tail Structures & Multi-Version**: Niche Resources (`que-*`, `CapabilityStatement`, `TestScript`, `ConceptMap`, `MedicinalProduct*`), `R4B`/`R5` Targets | [`generate_models.py`](../scripts/generate_models.py), [`resources.py`](../src/fhirlance/resources.py) |

---

## Forensic Audit: Where We Stand Today

| Capability Dimension | Current State in FHIRlance | Remaining Gap vs. `validator_cli.jar` |
| :--- | :--- | :--- |
| **Base R4 Structural** | 146 resources + 39 datatypes in [`resources.py`](../src/fhirlance/resources.py) & [`types.py`](../src/fhirlance/types.py) | **Complete** (`extra="forbid"`, strict primitives, `[x]` exclusivity, `_primitive` extensions). |
| **Terminology** | **1,161** complete CodeSystems (incl. `hl7.terminology.r4#6.2.0` UTG), **3,297** ValueSets, complex datatype element bindings (`COMPLEX_TYPE_BINDINGS`), offline grammars (UCUM, BCP-47, BCP-13, ISO-3166), L1/L2 SQLite cache, `--tx`, `--strict-extensible` ([`terminology.md`](terminology.md)) | Versioned canonicals (`url\|version`), `CodeSystem.supplements`, `exists`/`generalizes`/`child-of` filters, `ConceptMap`/`$translate`, and `--best-practice` (`preferred` bindings). |
| **Extensions** | First-class Extension `StructureDefinition` validation in [`extension_spec.py`](../src/fhirlance/extension_spec.py) & [`extensions.py`](../src/fhirlance/extensions.py) (`ext-1`, `context`, `value[x]`, sub-extensions, `modifierExtension` `isModifier` & unknown modifier rejection) | Arbitrary FHIRPath `ElementDefinition.constraint` rules declared on custom extensions. |
| **Slicing** | Complete slicing in [`slicing_spec.py`](../src/fhirlance/slicing_spec.py) & [`profile_engine.py`](../src/fhirlance/profile_engine.py): all 5 discriminator types (`value`, `pattern`, `type`, `profile`, `exists`), slice `min`/`max`, `closed`/`openAtEnd`/`ordered`, and nested sub-slicing | — |
| **Profile Engine** | 183 compiled profiles in [`profiles.py`](../src/fhirlance/profiles.py) + runtime `-ig` in [`ig_loader.py`](../src/fhirlance/ig_loader.py) | Transitive `package.json` IG `dependencies` auto-resolution, `fhirlance pkg install`, `unknown-profile` warning/error, `maxLength`, `minValue`/`maxValue`, `type.profile`, and `--enforce-must-support`. |
| **Bundles & References** | Outer `Bundle` validation in [`dataset.py`](../src/fhirlance/dataset.py); per-Bundle `fullUrl` & `#contained` symbol table in [`resource_validator.py`](../src/fhirlance/resource_validator.py) & [`profile_engine.py`](../src/fhirlance/profile_engine.py) (`Reference.type`, `targetProfile`, `aggregation`) | `bdl-6`, external/remote reference resolution beyond `Bundle` & `#contained`. |
| **FHIRPath Invariants** | 16 compiled invariant checks in [`invariants.py`](../src/fhirlance/invariants.py) (`txt-1`, `pat-1`, `obs-6/7`, `con-4`, `bdl-1..5`, `bdl-7..12`) + `ext-1` | General FHIRPath-to-Python compiler for `dom-1..6`, `ref-1`, `bdl-6`, `obs-*`, `pat-*`, `que-*`, and arbitrary IG `ElementDefinition.constraint` rules. |
| **Output & Server Ecosystem** | `OperationOutcome`, SARIF v2.1.0, JUnit XML, JSON & text ([`formatters.py`](../src/fhirlance/formatters.py)); intra-file multiprocessing ([`dataset.py`](../src/fhirlance/dataset.py)) | `fhirlance serve` UDS/HTTP daemon, HAPI FHIR / Smile CDR raw-byte interceptor, `mmap` streaming, and Rust C-ABI / Panama FFI. |

---

## Tier 1: Highest-Footprint Core Structures (`v0.2.0` — Done)

These structures appear in **>80% of real-world FHIR payloads** (US Core, IPS, CA-Baseline, Ontario MI/eReferral `Patient`, `Observation`, `DiagnosticReport`, `Condition`, `ServiceRequest`, `Bundle`). All four pillars are implemented and verified on `main`:

1. **First-Class Extension `StructureDefinition` Validation** *(Done — #17, #18)*
   - Extracts all `StructureDefinition`s where `type == "Extension"` across built-in IGs ([`generate_models.py`](../scripts/generate_models.py)) and runtime `-ig` packages ([`ig_loader.py`](../src/fhirlance/ig_loader.py)).
   - Validates extension `context`, `value[x]` allowed types and ValueSet bindings, complex extension sub-slices, and `modifierExtension` `isModifier` / unknown-modifier rules ([`extension_spec.py`](../src/fhirlance/extension_spec.py), [`extensions.py`](../src/fhirlance/extensions.py)).
2. **Complete Slicing Semantics & Slice `max` Cardinality** *(Done — #21)*
   - Supports all 5 FHIR discriminator types (`value`, `pattern`, `type`, `profile`, `exists`), slice `max`, `closed` / `openAtEnd` / `ordered` rules, and multi-level nested sub-slicing ([`slicing_spec.py`](../src/fhirlance/slicing_spec.py), [`profile_engine.py`](../src/fhirlance/profile_engine.py)).
3. **Bundle Reference Graph, `targetProfile` & Outer `Bundle` Validation** *(Done — #22)*
   - Validates the outer `Bundle` resource in [`dataset.py`](../src/fhirlance/dataset.py) and enforces `bdl-1`–`bdl-5`, `bdl-7`–`bdl-12` in [`invariants.py`](../src/fhirlance/invariants.py).
   - Indexes `entry[].fullUrl` and `contained[].id` (`#id`) to verify `Reference.type`, `targetProfile` conformance, and `type.aggregation` (`contained`, `referenced`, `bundled`).
4. **Complex Datatype Element Bindings & Single-Pass Scan** *(Done — #23, #24)*
   - Extracts and enforces ValueSet bindings declared on the 39 complex datatype `StructureDefinition`s (`COMPLEX_TYPE_BINDINGS`) via single-pass coding/extension traversal in [`resource_validator.py`](../src/fhirlance/resource_validator.py) and [`terminology.py`](../src/fhirlance/terminology.py).

---

## Tier 2: High-Footprint Conformance, FHIRPath & IG Ecosystem (`v0.3.0` — Next #1)

1. **AOT + Zero-`exec` Combinator FHIRPath Constraint Evaluator**
   - Generate direct Python functions in [`generate_models.py`](../scripts/generate_models.py) for built-in R4 and compiled IG `ElementDefinition.constraint.expression` rules (`dom-1..6`, `ref-1`, `bdl-6`, `obs-*`, `pat-*`, `con-*`, `med-*`, `us-core-*`, `ips-*`), paired with a safe, zero-`exec` AST-combinator/pattern evaluator in [`invariants.py`](../src/fhirlance/invariants.py) for runtime `-ig` packages (avoiding `exec()`/`compile()` and external runtime dependencies).
   - Add opt-in `--best-practice` flag for non-blocking HL7 best-practice recommendations (`dom-6` narrative, `Observation.performer`, `preferred` ValueSet bindings).
2. **Remaining `ElementDefinition` Constraints**
   - Extract and enforce `maxLength`, `minValue[x]` / `maxValue[x]`, `type.profile` (profiled datatypes such as `SimpleQuantity`, `Money`, `Age`, `Duration`), empty-list `min >= 1` edge cases, and optional `--enforce-must-support`.
3. **Transitive IG & Terminology Completeness**
   - Automatically resolve transitive `package.json` `dependencies` in `ig_loader.py` and `generate_models.py`, plus persistent disk caching in `~/.cache/fhirlance/` and `fhirlance pkg install <id>#<version>` (fetching from `packages.fhir.org` / Simplifier).
   - Support versioned canonicals (`url|version`) in `VALUE_SET_SPECS` / `COMPLETE_CODE_SYSTEMS`, `CodeSystem.supplements`, `ValueSet.compose.include.filter` (`exists`, `generalizes`, `child-of`), and configurable `unknown-profile` warnings/errors.

---

## Tier 3: Server Sidecar, HAPI / Smile CDR & Enterprise Scale (`v0.4.0`)

1. **`fhirlance serve` — Persistent `$validate` Sidecar Daemon**
   - **Unix Domain Sockets** (`fhirlance serve --uds /run/fhirlance.sock`) and HTTP (`--host 127.0.0.1 --port 8080`) with pre-forked workers (`--workers N`).
   - Exposes `POST /$validate`, `POST /{resourceType}/$validate`, `POST /$validate-batch`, `GET /healthz`, `GET /igs`, `HTTP 204 No Content` / `HTTP 422` fast paths, `validate_resource_detailed()`, and `--watch`.
2. **HAPI FHIR / Smile CDR Raw-Byte Interceptor & Edge Filter**
   - Hooks `Pointcut.SERVER_INCOMING_REQUEST_POST_PROCESSED` (and Smile CDR `CHANNEL_IMPORT`) to stream raw UTF-8 request bytes over UDS to `fhirlance serve` before Jackson/DOM parsing or `FhirInstanceValidator` runs (`< 0.3 ms`).
   - Reference Envoy / NGINX edge filter configs and Kubernetes sidecar / Docker Compose manifests.
3. **Memory-Mapped (`mmap`) Streaming NDJSON**
   - Byte-offset chunking for multi-gigabyte `.ndjson` files with `--stream` $O(1)$-memory output.

---

## Tier 4: Long-Tail Structures & Multi-Version (`v1.0.0`)

Lower-frequency R4 resources and long-term platform targets:

1. **Long-Tail / Specialized FHIR R4 Resources & Terminologies**
   - `Questionnaire` / `QuestionnaireResponse` (`que-*` invariants and `enableWhen` / `answerOption` checks), `CapabilityStatement` / `OperationDefinition` / `SearchParameter`, `ConceptMap` (`$translate`), `TestScript`, `StructureMap`, `GraphDefinition`, `Subscription`, `MolecularSequence`, `MedicinalProduct*`, and `VerificationResult`.
2. **Multi-Version FHIR Support (`R4B` & `R5`)**
   - Parameterize [`generate_models.py`](../scripts/generate_models.py) to emit versioned schema modules (`fhirlance.r4`, `fhirlance.r4b`, `fhirlance.r5`).

> [!NOTE]
> **Deferred: Native Rust C-ABI (`libfhirlance`) + Java Panama FFI**
> A standalone Rust rewrite (`libfhirlance` + `PyO3` + `java.lang.foreign.Linker`) is **intentionally deferred**. At ~118 µs/resource (~8,500 res/s per core), Python + `pydantic-core` already outperforms downstream FHIR server database writes and search indexing; keeping the validation engine in pure Python avoids a two-language maintenance tax and cross-platform native wheel complexity. Revisit only if a concrete deployment requires zero-sidecar in-process JVM embedding without `fhirlance serve`.

---

## License
Copyright (c) 2026 **Brightwood Consulting Group Limited**. Licensed under **[CC BY-NC 4.0](../LICENSE)**.
