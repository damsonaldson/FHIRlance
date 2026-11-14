# FHIRlance — Project Rules & Agent Workflow

## 1. Git, Commit & Pull Request Management
- **Agent-Managed VCS & PRs**: The agent manages all git branches, commits, pull requests, Dependabot updates, and merges for `damsonaldson/FHIRlance`.
- **Commit Style**: Use Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `ci:`, `chore:`).
- **Pre-Commit / Pre-Merge Local Quality Gate**: Before creating a commit or merging a PR, verify that all local checks pass cleanly using `.venv\Scripts\python.exe`:
  1. `ruff check .`
  2. `ruff format --check .`
  3. `mypy`
  4. `pytest -m "not hl7_live" --cov --cov-report=term-missing --cov-fail-under=95`
- **Branch Protection (`main`)**:
  - `main` is protected against force-pushes and branch deletion.
  - Required status checks on `main`: `Lint, Format & Type Check`, `Dependency Audit`, `Build & Smoke Test Distribution` (which transitively gates on all 8 OS/Python `Test (...)` matrix jobs), and `Analyze (Python)` (CodeQL).
  - Required approving reviews: `0` (solo maintainer workflow).
  - `Automated AI Code Review` (`.github/workflows/ai-review.yml`, using `models/gemini-3.8-flash`) runs on same-repo PRs as an advisory review comment and is intentionally non-blocking.

## 2. Core Engineering Guardrails
1. **Keep the Hot Path in Rust (`pydantic-core`)**:
   - **NEVER** add `@model_validator(mode="before")` to `FHIRBaseModel` in `src/fhirlance/base.py`.
   - Enforce structural rules via native Pydantic v2 annotations (`StringConstraints`, `Field(min_length=1)`, `Literal[...]`, `extra="forbid"`).
   - Handle `_primitive` JSON extensions lazily in `src/fhirlance/primitive_extensions.py` only after `extra="forbid"` reports an `extra_forbidden` key starting with `_`.
2. **Never Hand-Edit Generated Schema Modules**:
   - `src/fhirlance/types.py` (39 datatypes), `src/fhirlance/resources.py` (146 R4 resources), and `src/fhirlance/profiles.py` (multi-IG constraints) are compiled by `scripts/generate_models.py` from `~/.fhir/packages/`.
   - Always modify `scripts/generate_models.py` and re-run it rather than editing those three files directly.
3. **Clean Code & Strict Typing (Robert C. Martin / SOLID)**:
   - Keep functions single-purpose and shallowly nested using guard clauses / early returns.
   - Respect Ruff complexity limits enforced in `pyproject.toml`: McCabe complexity ≤ 10, max 5 arguments, max 10 branches, max 35 statements, max 6 return statements.
   - Maintain 100% strict `mypy` compliance (`strict = true`, `pydantic.mypy` plugin) across `src/fhirlance`, `scripts`, and `tests`.
   - Prefer `@dataclass(frozen=True, slots=True)` over untyped `dict[str, Any]` structures inside validation engines.
   - Catch only specific, expected exception types; never swallow unexpected exceptions silently.
4. **Test Coverage & HL7 `validator_cli.jar` Equivalence**:
   - Handwritten modules in `src/fhirlance/` must maintain **≥ 95% branch coverage** (`--cov-fail-under=95`).
   - Any change affecting FHIR R4 structural, FHIRPath invariant, or IG profile validation semantics must preserve parity with the official HL7 `validator_cli.jar` (`pytest -m hl7_live`).

## 3. Licensing & Attribution
- Licensed under **CC BY-NC 4.0** (`LICENSE`), Copyright (c) 2026 **Brightwood Consulting Group Limited**.
