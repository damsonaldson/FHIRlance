"""Exhaustive tests for all 54 FHIR R4 complex datatype models, 11 primitives, and 176 bindings."""

from __future__ import annotations

import inspect
import re
import types as py_types
import typing
from typing import TYPE_CHECKING, Any, Literal, Union, get_args, get_origin

import pytest
from pydantic import TypeAdapter, ValidationError

from fhirlance import RESOURCE_MODELS, FHIRBaseModel, validate_resource
from fhirlance import types as fhir_types
from fhirlance.base import (
    ExtensionBase,
    FHIRCode,
    FHIRDate,
    FHIRDateTime,
    FHIRDecimal,
    FHIRId,
    FHIRInstant,
    FHIRInteger,
    FHIRPositiveInt,
    FHIRString,
    FHIRTime,
    FHIRUnsignedInt,
    StrictBool,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

_VALUE_ERROR_RE = re.compile(r"ValueError\(['\"]([^'\"]+)['\"]\)")
_MINIMAL_CACHE: dict[type[FHIRBaseModel], dict[str, Any]] = {}
_META_PATTERNS: tuple[tuple[str, Any], ...] = (
    ("_check_fhir_date", "2026-01-15"),
    ("T([01][0-9]|2[0-3])", "2026-01-15T10:00:00Z"),
    ("^([01][0-9]|2[0-3]):[0-5][0-9]", "10:00:00"),
    ("{1,64}", "id-1"),
)


def _sample_value(ann: Any, metadata: Sequence[Any] = ()) -> Any:
    meta_str = " ".join(repr(m) for m in metadata) + " " + repr(ann)
    origin = get_origin(ann)
    args = get_args(ann)
    if origin in (Union, py_types.UnionType):
        non_none = [a for a in args if a is not type(None)]
        return _sample_value(non_none[0], metadata)
    if origin is typing.Annotated:
        return _sample_value(args[0], [*metadata, *args[1:]])
    if origin is Literal:
        return args[0]
    if origin is list:
        return [_sample_value(args[0])]
    if isinstance(ann, type) and issubclass(ann, FHIRBaseModel):
        return (
            {"url": "http://example.org/ext", "valueString": "ok"}
            if ann.__name__ == "Extension"
            else (dict(_build_minimal(ann)) or {"id": "sub-1"})
        )
    return _sample_primitive(ann, meta_str)


def _sample_primitive(ann: Any, meta_str: str) -> Any:
    for pattern, sample in _META_PATTERNS:
        if pattern in meta_str:
            return sample
    if "_check_int_not_bool" in meta_str or ann is int or "Int" in meta_str:
        return 1
    if ann is bool or "StrictBool" in meta_str:
        return True
    if ann is float or "Float" in meta_str or "Decimal" in meta_str:
        return 1.0
    return "sample-str"


def _build_minimal(model_cls: type[FHIRBaseModel]) -> dict[str, Any]:
    if model_cls in _MINIMAL_CACHE:
        return dict(_MINIMAL_CACHE[model_cls])
    hints = typing.get_type_hints(model_cls, include_extras=True)
    out: dict[str, Any] = {}
    for name, info in model_cls.model_fields.items():
        alias = info.alias or name
        ann = hints.get(name, info.annotation)
        if name == "resourceType":
            out["resourceType"] = get_args(ann)[0]
            continue
        if info.is_required():
            out[alias] = _sample_value(ann, info.metadata)

    mvs = model_cls.__pydantic_decorators__.model_validators
    if "_check_choices" in mvs:
        src = inspect.getsource(mvs["_check_choices"].func)
        first_var = ""
        for line in src.splitlines():
            if "_present = sum" in line:
                tup_str = line.split("for _f in (")[1].split(",)")[0]
                first_var = tup_str.split(",")[0].strip().strip("'\"")
            elif "_present != 1" in line:
                info = model_cls.model_fields[first_var]
                out[info.alias or first_var] = _sample_value(
                    hints.get(first_var, info.annotation),
                    info.metadata,
                )
    _MINIMAL_CACHE[model_cls] = dict(out)
    return out


_COMPLEX_TYPE_CLASSES: list[tuple[str, type[FHIRBaseModel]]] = [
    (name, cls)
    for name, cls in sorted(vars(fhir_types).items())
    if isinstance(cls, type)
    and issubclass(cls, FHIRBaseModel)
    and cls not in (FHIRBaseModel, ExtensionBase)
]


def _collect_root_literal_fields() -> list[tuple[str, str, tuple[str, ...], bool]]:
    """Return (resourceType, json_field_name, allowed_codes, is_list) for all Literal fields."""
    out: list[tuple[str, str, tuple[str, ...], bool]] = []
    for rtype, cls in sorted(RESOURCE_MODELS.items()):
        hints = typing.get_type_hints(cls, include_extras=True)
        for fname, info in cls.model_fields.items():
            if fname == "resourceType":
                continue
            ann = hints.get(fname, info.annotation)
            is_list = False
            while get_origin(ann) in (Union, py_types.UnionType, typing.Annotated, list):
                if get_origin(ann) is list:
                    is_list = True
                args = [a for a in get_args(ann) if a is not type(None)]
                ann = args[0]
            if get_origin(ann) is Literal:
                out.append((rtype, info.alias or fname, tuple(get_args(ann)), is_list))
    return out


_ROOT_LITERAL_FIELDS = _collect_root_literal_fields()

_PRIMITIVE_CASES: list[tuple[str, Any, Any, bool]] = [
    # FHIRDate: valid YYYY, YYYY-MM, YYYY-MM-DD, leap year Feb 29
    ("FHIRDate_year", FHIRDate, "1990", True),
    ("FHIRDate_year_month", FHIRDate, "2026-11", True),
    ("FHIRDate_full", FHIRDate, "2026-11-14", True),
    ("FHIRDate_leap_2024", FHIRDate, "2024-02-29", True),
    ("FHIRDate_leap_2000", FHIRDate, "2000-02-29", True),
    # FHIRDate: invalid calendar dates, formats, and types
    ("FHIRDate_non_leap_2023", FHIRDate, "2023-02-29", False),
    ("FHIRDate_non_leap_1900", FHIRDate, "1900-02-29", False),
    ("FHIRDate_feb_30", FHIRDate, "2026-02-30", False),
    ("FHIRDate_apr_31", FHIRDate, "2026-04-31", False),
    ("FHIRDate_jun_31", FHIRDate, "2026-06-31", False),
    ("FHIRDate_sep_31", FHIRDate, "2026-09-31", False),
    ("FHIRDate_nov_31", FHIRDate, "2026-11-31", False),
    ("FHIRDate_month_00", FHIRDate, "2026-00-15", False),
    ("FHIRDate_month_13", FHIRDate, "2026-13-15", False),
    ("FHIRDate_day_00", FHIRDate, "2026-01-00", False),
    ("FHIRDate_day_32", FHIRDate, "2026-01-32", False),
    ("FHIRDate_slash", FHIRDate, "2026/01/15", False),
    ("FHIRDate_single_digit_month", FHIRDate, "2026-1-15", False),
    ("FHIRDate_with_time", FHIRDate, "2026-01-15T10:00:00Z", False),
    ("FHIRDate_int", FHIRDate, 20260115, False),
    ("FHIRDate_empty", FHIRDate, "", False),
    # FHIRDateTime: valid partial and full timestamps with timezone
    ("FHIRDateTime_year", FHIRDateTime, "2026", True),
    ("FHIRDateTime_year_month", FHIRDateTime, "2026-05", True),
    ("FHIRDateTime_date", FHIRDateTime, "2026-05-15", True),
    ("FHIRDateTime_utc", FHIRDateTime, "2026-05-15T14:30:00Z", True),
    ("FHIRDateTime_frac_utc", FHIRDateTime, "2026-05-15T14:30:00.123456Z", True),
    ("FHIRDateTime_offset_neg", FHIRDateTime, "2026-05-15T14:30:00-04:00", True),
    ("FHIRDateTime_offset_pos", FHIRDateTime, "2026-05-15T14:30:00+05:30", True),
    ("FHIRDateTime_offset_max", FHIRDateTime, "2026-05-15T14:30:00+14:00", True),
    ("FHIRDateTime_leap_sec", FHIRDateTime, "2026-12-31T23:59:60Z", True),
    # FHIRDateTime: invalid missing timezone, out-of-range components
    ("FHIRDateTime_no_tz", FHIRDateTime, "2026-05-15T14:30:00", False),
    ("FHIRDateTime_hour_24", FHIRDateTime, "2026-05-15T24:00:00Z", False),
    ("FHIRDateTime_min_60", FHIRDateTime, "2026-05-15T14:60:00Z", False),
    ("FHIRDateTime_sec_61", FHIRDateTime, "2026-05-15T14:30:61Z", False),
    ("FHIRDateTime_tz_15", FHIRDateTime, "2026-05-15T14:30:00+15:00", False),
    ("FHIRDateTime_tz_14_30", FHIRDateTime, "2026-05-15T14:30:00+14:30", False),
    ("FHIRDateTime_year_0000", FHIRDateTime, "0000-01-01", False),
    ("FHIRDateTime_int", FHIRDateTime, 20260515, False),
    # FHIRInstant: valid full precision with timezone required
    ("FHIRInstant_utc", FHIRInstant, "2026-05-15T14:30:00Z", True),
    ("FHIRInstant_frac", FHIRInstant, "2026-05-15T14:30:00.999-04:00", True),
    ("FHIRInstant_tz_14", FHIRInstant, "2026-05-15T00:00:00+14:00", True),
    ("FHIRInstant_leap_sec", FHIRInstant, "2026-12-31T23:59:60Z", True),
    # FHIRInstant: invalid partial dates or missing timezone
    ("FHIRInstant_date_only", FHIRInstant, "2026-05-15", False),
    ("FHIRInstant_year_month", FHIRInstant, "2026-05", False),
    ("FHIRInstant_year_only", FHIRInstant, "2026", False),
    ("FHIRInstant_no_tz", FHIRInstant, "2026-05-15T14:30:00", False),
    ("FHIRInstant_no_seconds", FHIRInstant, "2026-05-15T14:30Z", False),
    # FHIRTime: valid hh:mm:ss(.fff) without timezone
    ("FHIRTime_midnight", FHIRTime, "00:00:00", True),
    ("FHIRTime_end_of_day", FHIRTime, "23:59:59", True),
    ("FHIRTime_leap_sec", FHIRTime, "23:59:60", True),
    ("FHIRTime_fractional", FHIRTime, "12:34:56.789", True),
    # FHIRTime: invalid timezone suffix or out-of-range
    ("FHIRTime_with_z", FHIRTime, "12:34:56Z", False),
    ("FHIRTime_with_offset", FHIRTime, "12:34:56-04:00", False),
    ("FHIRTime_hour_24", FHIRTime, "24:00:00", False),
    ("FHIRTime_min_60", FHIRTime, "12:60:00", False),
    ("FHIRTime_sec_61", FHIRTime, "12:00:61", False),
    ("FHIRTime_no_seconds", FHIRTime, "12:34", False),
    ("FHIRTime_single_hour", FHIRTime, "9:30:00", False),
    # FHIRId: 1..64 chars of [A-Za-z0-9-.]
    ("FHIRId_single", FHIRId, "a", True),
    ("FHIRId_max_64", FHIRId, "A" * 64, True),
    ("FHIRId_mixed", FHIRId, "pat-123.abc-XYZ.99", True),
    ("FHIRId_empty", FHIRId, "", False),
    ("FHIRId_65_chars", FHIRId, "A" * 65, False),
    ("FHIRId_space", FHIRId, "pat 1", False),
    ("FHIRId_underscore", FHIRId, "pat_1", False),
    ("FHIRId_slash", FHIRId, "Patient/1", False),
    ("FHIRId_colon", FHIRId, "urn:uuid:1", False),
    # FHIRCode: non-empty tokens separated by single space
    ("FHIRCode_simple", FHIRCode, "final", True),
    ("FHIRCode_hyphen", FHIRCode, "in-progress", True),
    ("FHIRCode_single_spaces", FHIRCode, "code one two", True),
    ("FHIRCode_empty", FHIRCode, "", False),
    ("FHIRCode_leading_space", FHIRCode, " final", False),
    ("FHIRCode_trailing_space", FHIRCode, "final ", False),
    ("FHIRCode_double_space", FHIRCode, "code  two", False),
    ("FHIRCode_leading_tab", FHIRCode, "\tcode", False),
    ("FHIRCode_trailing_newline", FHIRCode, "code\n", False),
    ("FHIRCode_double_tab", FHIRCode, "code\t\ttwo", False),
    ("FHIRCode_whitespace_only", FHIRCode, "   ", False),
    # FHIRPositiveInt: >= 1, no bool, no float, no str
    ("FHIRPositiveInt_1", FHIRPositiveInt, 1, True),
    ("FHIRPositiveInt_large", FHIRPositiveInt, 999999, True),
    ("FHIRPositiveInt_0", FHIRPositiveInt, 0, False),
    ("FHIRPositiveInt_neg", FHIRPositiveInt, -1, False),
    ("FHIRPositiveInt_bool_true", FHIRPositiveInt, True, False),
    ("FHIRPositiveInt_bool_false", FHIRPositiveInt, False, False),
    ("FHIRPositiveInt_float", FHIRPositiveInt, 1.0, False),
    ("FHIRPositiveInt_str", FHIRPositiveInt, "1", False),
    # FHIRUnsignedInt: >= 0, no bool, no float, no str
    ("FHIRUnsignedInt_0", FHIRUnsignedInt, 0, True),
    ("FHIRUnsignedInt_1", FHIRUnsignedInt, 1, True),
    ("FHIRUnsignedInt_large", FHIRUnsignedInt, 100000, True),
    ("FHIRUnsignedInt_neg", FHIRUnsignedInt, -1, False),
    ("FHIRUnsignedInt_bool_true", FHIRUnsignedInt, True, False),
    ("FHIRUnsignedInt_bool_false", FHIRUnsignedInt, False, False),
    ("FHIRUnsignedInt_float", FHIRUnsignedInt, 0.0, False),
    ("FHIRUnsignedInt_str", FHIRUnsignedInt, "0", False),
    # FHIRInteger: 32-bit signed int [-2147483648, 2147483647], no bool, no float, no str
    ("FHIRInteger_neg", FHIRInteger, -42, True),
    ("FHIRInteger_0", FHIRInteger, 0, True),
    ("FHIRInteger_pos", FHIRInteger, 42, True),
    ("FHIRInteger_min32", FHIRInteger, -2147483648, True),
    ("FHIRInteger_max32", FHIRInteger, 2147483647, True),
    ("FHIRInteger_under_min32", FHIRInteger, -2147483649, False),
    ("FHIRInteger_over_max32", FHIRInteger, 2147483648, False),
    ("FHIRInteger_bool_true", FHIRInteger, True, False),
    ("FHIRInteger_bool_false", FHIRInteger, False, False),
    ("FHIRInteger_float", FHIRInteger, 42.0, False),
    ("FHIRInteger_str", FHIRInteger, "42", False),
    # FHIRString: max 1048576 chars
    ("FHIRString_ok", FHIRString, "hello", True),
    ("FHIRString_max_len", FHIRString, "a" * 1048576, True),
    ("FHIRString_over_max_len", FHIRString, "a" * 1048577, False),
    ("FHIRString_int", FHIRString, 123, False),
    # FHIRDecimal: int or float, no bool, no NaN/Inf, no str
    ("FHIRDecimal_float", FHIRDecimal, 3.14159, True),
    ("FHIRDecimal_neg_float", FHIRDecimal, -0.005, True),
    ("FHIRDecimal_int", FHIRDecimal, 100, True),
    ("FHIRDecimal_bool_true", FHIRDecimal, True, False),
    ("FHIRDecimal_bool_false", FHIRDecimal, False, False),
    ("FHIRDecimal_str", FHIRDecimal, "3.14", False),
    # StrictBool: only True/False
    ("StrictBool_true", StrictBool, True, True),
    ("StrictBool_false", StrictBool, False, True),
    ("StrictBool_int_1", StrictBool, 1, False),
    ("StrictBool_int_0", StrictBool, 0, False),
    ("StrictBool_str", StrictBool, "true", False),
]


@pytest.mark.parametrize(
    ("name", "model_cls"),
    _COMPLEX_TYPE_CLASSES,
    ids=[name for name, _ in _COMPLEX_TYPE_CLASSES],
)
def test_every_complex_datatype_valid_and_structural_rules(
    name: str,
    model_cls: type[FHIRBaseModel],
) -> None:
    """Every complex datatype and BackboneElement in types.py enforces R4 structural rules."""
    valid_payload = (
        {"url": "http://example.org/ext", "valueString": "ok"}
        if name == "Extension"
        else _build_minimal(model_cls)
    )
    instance = model_cls.model_validate(valid_payload)
    assert isinstance(instance, model_cls)

    with pytest.raises(ValidationError):
        model_cls.model_validate({**valid_payload, "unknownComplexFieldXYZ": 1})

    required = [
        info.alias or fname for fname, info in model_cls.model_fields.items() if info.is_required()
    ]
    if required:
        with pytest.raises(ValidationError):
            model_cls.model_validate({})


@pytest.mark.parametrize(
    ("case_id", "prim_type", "value", "expected_valid"),
    _PRIMITIVE_CASES,
    ids=[c[0] for c in _PRIMITIVE_CASES],
)
def test_fhir_primitive_boundary_matrix(
    case_id: str,
    prim_type: Any,
    value: Any,
    expected_valid: bool,
) -> None:
    """Verify exact FHIR R4 regex, calendar, and strict type boundaries across all primitives."""
    adapter: TypeAdapter[Any] = TypeAdapter(prim_type)
    if expected_valid:
        assert adapter.validate_python(value) == value, f"{case_id} failed unexpectedly"
    else:
        with pytest.raises(ValidationError):
            adapter.validate_python(value)


@pytest.mark.parametrize(
    ("rtype", "field_name", "allowed_codes", "is_list"),
    _ROOT_LITERAL_FIELDS,
    ids=[f"{rt}.{fn}" for rt, fn, _, _ in _ROOT_LITERAL_FIELDS],
)
def test_every_r4_root_literal_code_binding(
    rtype: str,
    field_name: str,
    allowed_codes: tuple[str, ...],
    is_list: bool,
) -> None:
    """Every root resource field with a required ValueSet Literal binding enforces allowed codes."""
    base = _build_minimal(RESOURCE_MODELS[rtype])
    valid_val: Any = [allowed_codes[0]] if is_list else allowed_codes[0]
    ok_issues = validate_resource(
        {**base, field_name: valid_val},
    )
    assert not any(f"Structural[{field_name}" in i for i in ok_issues)

    bad_val: Any = ["__invalid_fhir_code__"] if is_list else "__invalid_fhir_code__"
    bad_issues = validate_resource(
        {**base, field_name: bad_val},
    )
    assert any(f"Structural[{field_name}" in i for i in bad_issues), (
        f"{rtype}.{field_name} accepted invalid code: {bad_issues}"
    )
