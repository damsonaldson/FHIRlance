"""Property-based fuzz tests (Hypothesis) and hot-path architecture guards."""

from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from fhirlance import FHIRBaseModel, loads_strict_json, validate_resource

_JSON_SCALARS = st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text()
_JSON_VALUES: st.SearchStrategy[Any] = st.recursive(
    _JSON_SCALARS,
    lambda children: (
        st.lists(children, max_size=5) | st.dictionaries(st.text(max_size=24), children, max_size=6)
    ),
    max_leaves=15,
)


@given(payload=_JSON_VALUES)
@settings(max_examples=100, deadline=None)
def test_validate_resource_never_crashes_on_arbitrary_json(payload: Any) -> None:
    """Arbitrary JSON structures must always yield a list[str], never an unhandled crash."""
    issues = validate_resource(payload)
    assert isinstance(issues, list)
    assert all(isinstance(msg, str) for msg in issues)


@given(
    resource_type=st.sampled_from(
        ["Patient", "Observation", "Condition", "Bundle", "Organization"]
    ),
    extra=st.dictionaries(st.text(min_size=1, max_size=20), _JSON_VALUES, max_size=6),
)
@settings(max_examples=100, deadline=None)
def test_validate_resource_handles_arbitrary_fields_on_real_resources(
    resource_type: str,
    extra: dict[str, Any],
) -> None:
    """Known resource types with arbitrary mutated fields never raise unhandled exceptions."""
    payload = {**extra, "resourceType": resource_type}
    issues = validate_resource(payload)
    assert isinstance(issues, list)
    assert all(isinstance(msg, str) for msg in issues)


@pytest.mark.parametrize("bad_literal", ["NaN", "Infinity", "-Infinity"])
def test_loads_strict_json_rejects_nonstandard_constants(bad_literal: str) -> None:
    raw = json.dumps({"resourceType": "Patient"})[:-1] + f', "x": {bad_literal}}}'
    with pytest.raises(ValueError, match="non-standard JSON"):
        loads_strict_json(raw)


def test_rust_hot_path_guard_and_throughput() -> None:
    """Guardrail #1: FHIRBaseModel must keep zero Python model_validators on the hot path."""
    assert not FHIRBaseModel.__pydantic_decorators__.model_validators

    patient = {
        "resourceType": "Patient",
        "id": "perf-1",
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1990-05-15",
    }
    # Warm up and verify 200 validations complete comfortably under 0.5s in Python/Rust.
    assert validate_resource(patient) == []
    t0 = time.perf_counter()
    for _ in range(200):
        assert validate_resource(patient) == []
    elapsed = time.perf_counter() - t0
    assert elapsed < 0.5, f"Hot-path throughput regression: 200 patients took {elapsed:.3f}s"


def _load_benchmark_script() -> Any:
    script_path = Path(__file__).resolve().parents[1] / "scripts" / "benchmark_performance.py"
    spec = importlib.util.spec_from_file_location("benchmark_performance", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_benchmark_performance_script_and_docs_sync() -> None:
    """Verify build-time benchmark script generates valid metrics and keeps docs synced."""
    mod = _load_benchmark_script()

    assert mod.BENCHMARK_JSON_PATH.exists()
    recorded = json.loads(mod.BENCHMARK_JSON_PATH.read_text(encoding="utf-8"))
    assert recorded["corpus_size"] == len(mod._load_master_325_corpus())
    assert recorded["r4_resource_types"] == 146
    assert recorded["compiled_ig_profiles"] == 198
    assert recorded["standard_mode"]["speedup_vs_hl7"] > 100.0
    assert recorded["operation_outcome_mode"]["speedup_vs_hl7"] > 100.0
    assert recorded["hl7_baseline_mode"]["elapsed_ms"] > 1000.0

    for doc_path in (mod.README_PATH, mod.EQUIV_DOC_PATH):
        text = doc_path.read_text(encoding="utf-8")
        assert mod.START_MARKER in text
        assert mod.END_MARKER in text
        assert "FHIRlance — Standard Mode" in text
        assert "FHIRlance — FHIR Output (`OperationOutcome`) Mode" in text
        assert "Official HL7 Baseline Validator" in text

    live_report = mod.run_benchmarks(run_hl7_live=False)
    md = mod.render_markdown_section(live_report)
    assert mod.START_MARKER in md
    assert mod.END_MARKER in md
    assert "validate_to_operation_outcome" in md
    assert "validator_cli.jar" in md
