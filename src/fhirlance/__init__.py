"""High-performance FHIR R4 structural and multi-IG profile validator."""

from fhirlance.base import DomainResourceBase, FHIRBaseModel
from fhirlance.conceptmap import (
    ConceptMapRegistry,
    ConceptMapSpec,
    TranslateMatch,
    TranslateRequest,
    TranslateResult,
    parse_concept_map,
    translate_code,
)
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
    load_compiled_ig_extensions,
    load_compiled_ig_profiles,
    load_ig_concept_maps,
    load_raw_ig_extensions,
    load_raw_ig_profiles,
    register_ig,
)
from fhirlance.profiles import EXTENSION_CONSTRAINTS, PROFILE_CONSTRAINTS
from fhirlance.resource_validator import validate_resource
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.terminology import (
    TerminologyResult,
    TxClient,
    TxOptions,
    parse_tx_options,
    validate_binding_value,
    validate_remote_code,
    validate_standalone_codings,
)
from fhirlance.validator import validate_dataset_structural

__version__ = "0.1.0"

__all__ = [
    "EXTENSION_CONSTRAINTS",
    "PROFILE_CONSTRAINTS",
    "RESOURCE_MODELS",
    "SUPPORTED_OUTPUT_FORMATS",
    "ConceptMapRegistry",
    "ConceptMapSpec",
    "DomainResourceBase",
    "FHIRBaseModel",
    "TerminologyResult",
    "TranslateMatch",
    "TranslateRequest",
    "TranslateResult",
    "TxClient",
    "TxOptions",
    "__version__",
    "clear_ig_cache",
    "dataset_to_junit_xml",
    "dataset_to_operation_outcome",
    "dataset_to_sarif",
    "format_dataset_report",
    "issues_to_operation_outcome",
    "load_compiled_ig_extensions",
    "load_compiled_ig_profiles",
    "load_ig_concept_maps",
    "load_raw_ig_extensions",
    "load_raw_ig_profiles",
    "loads_strict_json",
    "parse_concept_map",
    "parse_tx_options",
    "register_ig",
    "translate_code",
    "validate_binding_value",
    "validate_dataset",
    "validate_dataset_structural",
    "validate_remote_code",
    "validate_resource",
    "validate_standalone_codings",
    "validate_to_operation_outcome",
]
