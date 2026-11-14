"""Public validator facade preserving backward-compatible exports."""

from __future__ import annotations

from fhirlance.dataset import loads_strict_json, validate_dataset
from fhirlance.resource_validator import validate_resource

validate_structural_and_canadian = validate_resource
validate_dataset_structural = validate_dataset

__all__ = [
    "loads_strict_json",
    "validate_dataset",
    "validate_dataset_structural",
    "validate_resource",
    "validate_structural_and_canadian",
]
