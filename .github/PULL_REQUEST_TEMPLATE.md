## Summary
<!-- Briefly describe what this change does and why. -->

## Engineering Checklist
- [ ] **Rust hot path preserved**: No `@model_validator(mode="before")` added to `FHIRBaseModel`.
- [ ] **Codegen discipline**: Generated files (`types.py`, `resources.py`, `profiles.py`) were not hand-edited; any model/profile changes were made via `scripts/generate_models.py`.
- [ ] **Clean Code**: Functions are small, single-purpose, shallowly nested, and strictly typed.
- [ ] **Checks pass locally**:
  - `ruff check .`
  - `ruff format --check .`
  - `mypy`
  - `pytest -m "not hl7_live" --cov --cov-fail-under=95`
- [ ] **Live HL7 equivalence** (if validation semantics changed): `pytest -m hl7_live` passed against `validator_cli.jar`.
