"""Base Pydantic v2 models and strict FHIR R4 primitive types (Rust pydantic-core backed)."""

from __future__ import annotations

import re
from datetime import date
from typing import Annotated, Any

from pydantic import (
    AfterValidator,
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
    StringConstraints,
    ValidationInfo,
    model_validator,
)

FHIR_DATE_RE = re.compile(r"^-?[0-9]{4}(-(0[1-9]|1[0-2])(-(0[0-9]|[12][0-9]|3[01]))?)?$")
_FHIR_DATETIME_PATTERN = (
    r"^([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)"
    r"(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1])"
    r"(T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?"
    r"(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00)))?)?)?$"
)
_FHIR_INSTANT_PATTERN = (
    r"^([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)"
    r"-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])"
    r"T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?"
    r"(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))$"
)
_FHIR_TIME_PATTERN = r"^([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?$"
_FHIR_ID_PATTERN = r"^[A-Za-z0-9\-\.]{1,64}$"
_FHIR_CODE_PATTERN = r"^[^\s]+(\s[^\s]+)*$"

_ELEMENT_KEYS = frozenset({"id", "extension"})
_FULL_DATE_PARTS = 3


def _check_fhir_date(value: str) -> str:
    if not FHIR_DATE_RE.match(value):
        raise ValueError(f"Invalid FHIR date: '{value}'")
    parts = value.split("-")
    if len(parts) == _FULL_DATE_PARTS and not value.startswith("-"):
        date(int(parts[0]), int(parts[1]), int(parts[2]))
    return value


def _check_int_not_bool(value: int) -> int:
    # Python bool subclasses int; reject True/False on integer FHIR primitives.
    if type(value) is bool:
        raise ValueError("Expected integer, got boolean")
    return value


def validate_extension_item(ext: Any) -> None:
    """Enforce FHIR Extension rules and ext-1 (extension or value[x]/_value[x], not both)."""
    if type(ext) is not dict:
        raise ValueError("Extension must be an object")

    url = ext.get("url")
    if type(url) is not str or not url:
        raise ValueError("Extension.url is required and must be a non-empty string")

    sub_exts = ext.get("extension")
    has_ext = sub_exts is not None
    if has_ext:
        if type(sub_exts) is not list or not sub_exts:
            raise ValueError("Extension.extension must be a non-empty list")
        for sub in sub_exts:
            validate_extension_item(sub)

    has_val = any(
        (k.startswith("value") or k.startswith("_value")) and ext[k] is not None for k in ext
    )
    if has_ext == has_val:
        raise ValueError("ext-1: Extension MUST have either extensions or value[x], not both")


def validate_primitive_ext_obj(obj: Any, key: str) -> None:
    """Validate a single `_primitive` Element object."""
    if type(obj) is not dict or not obj:
        raise ValueError(f"Primitive extension '{key}' item must be a non-empty object")
    if not _ELEMENT_KEYS.issuperset(obj.keys()):
        extra_keys = sorted(set(obj.keys()) - _ELEMENT_KEYS)
        raise ValueError(f"Primitive extension '{key}' has unknown keys: {extra_keys}")
    if "extension" in obj:
        exts = obj["extension"]
        if type(exts) is not list or not exts:
            raise ValueError(f"Primitive extension '{key}.extension' must be a non-empty list")
        for ext in exts:
            validate_extension_item(ext)


# Native Rust pydantic-core constraints (zero Python callback overhead for common primitives)
FHIRDate = Annotated[StrictStr, AfterValidator(_check_fhir_date)]
FHIRDateTime = Annotated[StrictStr, StringConstraints(pattern=_FHIR_DATETIME_PATTERN)]
FHIRInstant = Annotated[StrictStr, StringConstraints(pattern=_FHIR_INSTANT_PATTERN)]
FHIRTime = Annotated[StrictStr, StringConstraints(pattern=_FHIR_TIME_PATTERN)]
FHIRId = Annotated[StrictStr, StringConstraints(pattern=_FHIR_ID_PATTERN)]
FHIRCode = Annotated[StrictStr, StringConstraints(pattern=_FHIR_CODE_PATTERN)]
FHIRPositiveInt = Annotated[StrictInt, Field(ge=1), AfterValidator(_check_int_not_bool)]
FHIRUnsignedInt = Annotated[StrictInt, Field(ge=0), AfterValidator(_check_int_not_bool)]
FHIRInteger = Annotated[
    StrictInt, Field(ge=-2147483648, le=2147483647), AfterValidator(_check_int_not_bool)
]
FHIRDecimal = StrictFloat | Annotated[StrictInt, AfterValidator(_check_int_not_bool)]
FHIRString = Annotated[StrictStr, StringConstraints(max_length=1048576)]

# Re-export StrictBool alongside primitives so generated models share one base module.
__all__ = [
    "FHIR_DATE_RE",
    "DomainResourceBase",
    "ExtensionBase",
    "FHIRBaseModel",
    "FHIRCode",
    "FHIRDate",
    "FHIRDateTime",
    "FHIRDecimal",
    "FHIRId",
    "FHIRInstant",
    "FHIRInteger",
    "FHIRPositiveInt",
    "FHIRString",
    "FHIRTime",
    "FHIRUnsignedInt",
    "StrictBool",
    "validate_extension_item",
    "validate_primitive_ext_obj",
]


class FHIRBaseModel(BaseModel):
    """Base model enforcing FHIR R4 structural rules (pure Rust pydantic-core hot path)."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, allow_inf_nan=False)


class ExtensionBase(FHIRBaseModel):
    """Base class for FHIR Extension enforcing the ext-1 invariant."""

    @model_validator(mode="before")
    @classmethod
    def _check_ext_1(cls, data: Any, info: ValidationInfo) -> Any:
        # Skip duplicate validation when primitive-extension fallback already checked this tree.
        if type(data) is dict and not (info.context and info.context.get("prim_exts_validated")):
            validate_extension_item(data)
        return data


class DomainResourceBase(FHIRBaseModel):
    """Shared base fields for all FHIR R4 DomainResource types."""

    id: FHIRId | None = None
    meta: Any = None
    implicitRules: StrictStr | None = None  # noqa: N815
    language: FHIRCode | None = None
    text: Any = None
    contained: list[dict[str, Any]] | None = None
    extension: list[Any] | None = None
    modifierExtension: list[Any] | None = None  # noqa: N815
