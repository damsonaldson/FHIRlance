"""High-performance FHIR R4 structural and multi-IG profile validator."""

from fhirlance.base import DomainResourceBase, FHIRBaseModel
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
from fhirlance.profiles import PROFILE_CONSTRAINTS
from fhirlance.resource_validator import validate_resource
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.validator import validate_dataset_structural, validate_structural_and_canadian

__version__ = "0.1.0"

__all__ = [
    "PROFILE_CONSTRAINTS",
    "RESOURCE_MODELS",
    "SUPPORTED_OUTPUT_FORMATS",
    "DomainResourceBase",
    "FHIRBaseModel",
    "__version__",
    "clear_ig_cache",
    "dataset_to_junit_xml",
    "dataset_to_operation_outcome",
    "dataset_to_sarif",
    "format_dataset_report",
    "issues_to_operation_outcome",
    "load_compiled_ig_profiles",
    "load_raw_ig_profiles",
    "loads_strict_json",
    "register_ig",
    "validate_dataset",
    "validate_dataset_structural",
    "validate_resource",
    "validate_structural_and_canadian",
    "validate_to_operation_outcome",
]
