"""Public validator facade preserving backward-compatible exports."""

from __future__ import annotations

from fhirlance.dataset import loads_strict_json, validate_dataset
from fhirlance.formatters import (
    SUPPORTED_OUTPUT_FORMATS,
    dataset_to_junit_xml,
    dataset_to_operation_outcome,
    dataset_to_sarif,
    format_dataset_report,
    issues_to_operation_outcome,
    validate_to_operation_outcome,
)
from fhirlance.ig_loader import (
    clear_ig_cache,
    load_compiled_ig_profiles,
    load_raw_ig_profiles,
    register_ig,
)
from fhirlance.resource_validator import validate_resource
from fhirlance.terminology import (
    TerminologyResult,
    TxClient,
    TxOptions,
    parse_tx_options,
    validate_binding_value,
    validate_remote_code,
    validate_standalone_codings,
)

validate_structural_and_canadian = validate_resource
validate_dataset_structural = validate_dataset

__all__ = [
    "SUPPORTED_OUTPUT_FORMATS",
    "TerminologyResult",
    "TxClient",
    "TxOptions",
    "clear_ig_cache",
    "dataset_to_junit_xml",
    "dataset_to_operation_outcome",
    "dataset_to_sarif",
    "format_dataset_report",
    "issues_to_operation_outcome",
    "load_compiled_ig_profiles",
    "load_raw_ig_profiles",
    "loads_strict_json",
    "parse_tx_options",
    "register_ig",
    "validate_binding_value",
    "validate_dataset",
    "validate_dataset_structural",
    "validate_remote_code",
    "validate_resource",
    "validate_standalone_codings",
    "validate_structural_and_canadian",
    "validate_to_operation_outcome",
]
