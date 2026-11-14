"""High-performance FHIR R4 structural and multi-IG profile validator."""

from fhirlance.base import DomainResourceBase, FHIRBaseModel
from fhirlance.dataset import loads_strict_json, validate_dataset
from fhirlance.profiles import PROFILE_CONSTRAINTS
from fhirlance.resource_validator import validate_resource
from fhirlance.resources import RESOURCE_MODELS
from fhirlance.validator import validate_dataset_structural, validate_structural_and_canadian

__all__ = [
    "PROFILE_CONSTRAINTS",
    "RESOURCE_MODELS",
    "DomainResourceBase",
    "FHIRBaseModel",
    "loads_strict_json",
    "validate_dataset",
    "validate_dataset_structural",
    "validate_resource",
    "validate_structural_and_canadian",
]
