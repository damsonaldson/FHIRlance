"""Comprehensive test suite covering all 146 FHIR R4 resource models."""

from __future__ import annotations

import pytest

from fhirlance import RESOURCE_MODELS, FHIRBaseModel, validate_resource


def test_all_146_r4_resources_registered() -> None:
    """Verify all 146 base FHIR R4 resource types are registered."""
    assert len(RESOURCE_MODELS) == 146
    for rtype, cls in RESOURCE_MODELS.items():
        assert issubclass(cls, FHIRBaseModel), f"{rtype} is not a FHIRBaseModel"


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_rejects_unknown_field_and_empty_array(rtype: str) -> None:
    """Every single one of the 146 R4 models must reject unknown fields and empty arrays."""
    issues_unknown = validate_resource({"resourceType": rtype, "nonExistentFhirFieldXYZ": "bad"})
    assert any("Structural[" in i for i in issues_unknown), (
        f"{rtype} allowed unknown field: {issues_unknown}"
    )

    model_cls = RESOURCE_MODELS[rtype]
    if "extension" in model_cls.model_fields:
        issues_empty = validate_resource({"resourceType": rtype, "extension": []})
        assert any("cannot be empty" in i or "at least 1 item" in i for i in issues_empty), (
            f"{rtype} allowed empty array for extension: {issues_empty}"
        )


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_enforces_required_fields(rtype: str) -> None:
    """Every R4 model with required fields beyond resourceType must reject a bare stub."""
    model_cls = RESOURCE_MODELS[rtype]
    required = [
        name
        for name, info in model_cls.model_fields.items()
        if name != "resourceType" and info.is_required()
    ]
    if not required:
        pytest.skip(f"{rtype} has no required fields beyond resourceType")

    issues = validate_resource({"resourceType": rtype})
    assert any("Field required" in i for i in issues), (
        f"{rtype} did not report missing required fields {required}: {issues}"
    )
