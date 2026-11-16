"""Comprehensive structural, primitive, invariant, and choice tests across all 146 R4 models."""

from __future__ import annotations

import inspect
import re
import types as py_types
import typing
from typing import TYPE_CHECKING, Any, Literal, Union, get_args, get_origin

import pytest
from pydantic import ValidationError

from fhirlance import RESOURCE_MODELS, DomainResourceBase, FHIRBaseModel, validate_resource
from fhirlance import resources as fhir_resources
from fhirlance import types as fhir_types

if TYPE_CHECKING:
    from collections.abc import Sequence

_VALUE_ERROR_RE = re.compile(r"ValueError\(['\"]([^'\"]+)['\"]\)")
_TYPE_HINTS_CACHE: dict[type[FHIRBaseModel], dict[str, Any]] = {}
_MINIMAL_VALID_CACHE: dict[type[FHIRBaseModel], dict[str, Any]] = {}


def _get_resolved_hints(model_cls: type[FHIRBaseModel]) -> dict[str, Any]:
    if model_cls not in _TYPE_HINTS_CACHE:
        _TYPE_HINTS_CACHE[model_cls] = typing.get_type_hints(model_cls, include_extras=True)
    return _TYPE_HINTS_CACHE[model_cls]


def extract_model_choices(
    model_cls: type[FHIRBaseModel],
) -> list[tuple[str, tuple[str, ...], bool]]:
    """Extract (raw_choice_name, variant_field_names, is_required) from a generated FHIR model."""
    mvs = model_cls.__pydantic_decorators__.model_validators
    if "_check_choices" not in mvs:
        return []
    src = inspect.getsource(mvs["_check_choices"].func)
    out: list[tuple[str, tuple[str, ...], bool]] = []
    variants: tuple[str, ...] = ()
    for line in src.splitlines():
        if "_present = sum" in line:
            tup_str = line.split("for _f in (")[1].split(",)")[0]
            variants = tuple(v.strip().strip("'\"") for v in tup_str.split(",") if v.strip())
        elif "raise ValueError(" in line:
            is_req = "_present != 1" in line
            match = _VALUE_ERROR_RE.search(line)
            raw_name = match.group(1).split(" ")[0] if match else "choice[x]"
            out.append((raw_name, variants, is_req))
    return out


_META_PATTERNS: tuple[tuple[str, Any], ...] = (
    ("_check_fhir_date", "2026-01-15"),
    ("T([01][0-9]|2[0-3])", "2026-01-15T10:00:00Z"),
    ("^([01][0-9]|2[0-3]):[0-5][0-9]", "10:00:00"),
    ("{1,64}", "id-1"),
)


def sample_value_for_field(ann: Any, metadata: Sequence[Any] = ()) -> Any:
    """Synthesize a valid minimal value for a resolved FHIR field annotation."""
    meta_str = " ".join(repr(m) for m in metadata) + " " + repr(ann)
    origin = get_origin(ann)
    args = get_args(ann)
    if origin in (Union, py_types.UnionType):
        non_none = [a for a in args if a is not type(None)]
        return sample_value_for_field(non_none[0], metadata)
    if origin is typing.Annotated:
        return sample_value_for_field(args[0], [*metadata, *args[1:]])
    if origin is Literal:
        return args[0]
    if origin is list:
        return [sample_value_for_field(args[0])]
    if isinstance(ann, type) and issubclass(ann, FHIRBaseModel):
        return (
            {"url": "http://example.org/ext", "valueString": "ok"}
            if ann.__name__ == "Extension"
            else (dict(build_minimal_valid(ann)) or {"id": "sub-1"})
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


def build_minimal_valid(model_cls: type[FHIRBaseModel]) -> dict[str, Any]:
    """Build a minimal structurally valid dictionary for any generated FHIRBaseModel class."""
    if model_cls in _MINIMAL_VALID_CACHE:
        return dict(_MINIMAL_VALID_CACHE[model_cls])
    hints = _get_resolved_hints(model_cls)
    out: dict[str, Any] = {}
    for name, info in model_cls.model_fields.items():
        alias = info.alias or name
        ann = hints.get(name, info.annotation)
        if name == "resourceType":
            out["resourceType"] = get_args(ann)[0]
            continue
        if not info.is_required():
            continue
        out[alias] = sample_value_for_field(ann, info.metadata)

    for _, variants, is_req in extract_model_choices(model_cls):
        if is_req:
            first_var = variants[0]
            info = model_cls.model_fields[first_var]
            ann = hints.get(first_var, info.annotation)
            out[info.alias or first_var] = sample_value_for_field(ann, info.metadata)

    if out.get("resourceType") == "CapabilityStatement":
        out["kind"] = "capability"
        out["software"] = {"name": "sample-sw"}
        out["rest"] = [{"mode": "server"}]

    _MINIMAL_VALID_CACHE[model_cls] = dict(out)
    return out


_ALL_GENERATED_CLASSES: list[type[FHIRBaseModel]] = [
    *[
        v
        for _, v in sorted(vars(fhir_resources).items())
        if isinstance(v, type) and issubclass(v, FHIRBaseModel)
    ],
    *[
        v
        for _, v in sorted(vars(fhir_types).items())
        if isinstance(v, type) and issubclass(v, FHIRBaseModel)
    ],
]

_ALL_CHOICE_CASES: list[tuple[type[FHIRBaseModel], str, tuple[str, ...], bool]] = [
    (cls, raw_name, variants, is_req)
    for cls in _ALL_GENERATED_CLASSES
    for raw_name, variants, is_req in extract_model_choices(cls)
]


def test_all_146_r4_resources_registered() -> None:
    """Verify all 146 base FHIR R4 resource types are registered and inherit FHIRBaseModel."""
    assert len(RESOURCE_MODELS) == 146
    for rtype, cls in RESOURCE_MODELS.items():
        assert issubclass(cls, FHIRBaseModel), f"{rtype} is not a FHIRBaseModel"


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_accepts_valid_minimal_instance(rtype: str) -> None:
    """Every single one of the 146 R4 models must accept a clean minimal valid instance."""
    model_cls = RESOURCE_MODELS[rtype]
    payload = build_minimal_valid(model_cls)
    issues = validate_resource(payload)
    assert issues == [], f"{rtype} rejected valid minimal instance: {issues}"


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_rejects_unknown_field_and_empty_array(rtype: str) -> None:
    """Every single one of the 146 R4 models must reject unknown fields and empty arrays."""
    base = build_minimal_valid(RESOURCE_MODELS[rtype])
    issues_unknown = validate_resource(
        {**base, "nonExistentFhirFieldXYZ": "bad"},
    )
    assert any("Structural[" in i for i in issues_unknown), (
        f"{rtype} allowed unknown field: {issues_unknown}"
    )

    model_cls = RESOURCE_MODELS[rtype]
    list_field = "extension" if "extension" in model_cls.model_fields else None
    if list_field is None:
        for fname, info in model_cls.model_fields.items():
            if "list[" in str(info.annotation):
                list_field = info.alias or fname
                break
    assert list_field is not None
    issues_empty = validate_resource({**base, list_field: []})
    assert any("at least 1 item" in i or "cannot be empty" in i for i in issues_empty), (
        f"{rtype} allowed empty array for {list_field}: {issues_empty}"
    )


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_rejects_invalid_id_and_primitives(rtype: str) -> None:
    """Every R4 resource must enforce strict FHIRId and primitive type constraints."""
    base = build_minimal_valid(RESOURCE_MODELS[rtype])
    bad_id_spaces = validate_resource(
        {**base, "id": "invalid id with spaces!"},
    )
    assert any("Structural[id]" in i for i in bad_id_spaces)

    bad_id_long = validate_resource({**base, "id": "a" * 65})
    assert any("Structural[id]" in i for i in bad_id_long)

    bad_id_type = validate_resource({**base, "id": 12345})
    assert any("Structural[id]" in i for i in bad_id_type)

    bad_lang = validate_resource(
        {**base, "language": "  leading-whitespace  "},
    )
    assert any("Structural[language]" in i for i in bad_lang)


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_domain_invariants_and_primitive_extensions(rtype: str) -> None:
    """Every R4 resource validates _primitive companion elements and DomainResource invariants."""
    model_cls = RESOURCE_MODELS[rtype]
    base = build_minimal_valid(model_cls)

    valid_prim_ext = {
        **base,
        "id": "res-1",
        "_id": {"extension": [{"url": "http://example.org/ext", "valueString": "v"}]},
    }
    assert validate_resource(valid_prim_ext) == []

    bad_prim_ext = {**base, "id": "res-1", "_id": {"unknownKey": 1}}
    assert any("Structural[_id]" in i for i in validate_resource(bad_prim_ext))

    if issubclass(model_cls, DomainResourceBase):
        bad_txt = {**base, "text": {"status": "generated", "div": "<span>no div</span>"}}
        assert any("Invariant[txt-1]" in i for i in validate_resource(bad_txt))
        bad_ext1 = {**base, "extension": [{"url": "http://example.org/empty"}]}
        assert any("ext-1" in i for i in validate_resource(bad_ext1))


@pytest.mark.parametrize("rtype", sorted(RESOURCE_MODELS.keys()))
def test_every_r4_resource_enforces_required_fields(rtype: str) -> None:
    """Every R4 model enforces required fields, or accepts bare resourceType if none required."""
    model_cls = RESOURCE_MODELS[rtype]
    required = [
        info.alias or name
        for name, info in model_cls.model_fields.items()
        if name != "resourceType" and info.is_required()
    ]
    req_choices = [raw for raw, _, is_req in extract_model_choices(model_cls) if is_req]
    issues = validate_resource({"resourceType": rtype})
    if required:
        assert any("Field required" in i for i in issues), (
            f"{rtype} did not report missing required fields {required}: {issues}"
        )
    elif req_choices:
        assert any("requires exactly one value" in i for i in issues), (
            f"{rtype} did not report missing required choice {req_choices}: {issues}"
        )
    else:
        assert issues == [], f"{rtype} has no required fields but rejected bare stub: {issues}"


@pytest.mark.parametrize(
    ("model_cls", "raw_name", "variants", "is_req"),
    _ALL_CHOICE_CASES,
    ids=[f"{cls.__name__}.{raw}" for cls, raw, _, _ in _ALL_CHOICE_CASES],
)
def test_every_generated_choice_group_exclusivity(
    model_cls: type[FHIRBaseModel],
    raw_name: str,
    variants: tuple[str, ...],
    is_req: bool,
) -> None:
    """Every [x] choice group across all 659 models enforces single-variant exclusivity."""
    hints = _get_resolved_hints(model_cls)
    base = (
        {"url": "http://example.org/ext"}
        if model_cls.__name__ == "Extension"
        else build_minimal_valid(model_cls)
    )
    for var_name in variants:
        base.pop(model_cls.model_fields[var_name].alias or var_name, None)

    f0 = model_cls.model_fields[variants[0]]
    k0 = f0.alias or variants[0]
    one_ok = {
        **base,
        k0: sample_value_for_field(hints.get(variants[0], f0.annotation), f0.metadata),
    }
    instance = model_cls.model_validate(one_ok)
    assert getattr(instance, variants[0]) is not None

    if len(variants) >= 2:
        f1 = model_cls.model_fields[variants[1]]
        k1 = f1.alias or variants[1]
        two_bad = {
            **one_ok,
            k1: sample_value_for_field(hints.get(variants[1], f1.annotation), f1.metadata),
        }
        with pytest.raises(ValidationError) as exc_info:
            model_cls.model_validate(two_bad)
        assert raw_name in str(exc_info.value) or "ext-1" in str(exc_info.value)

    if is_req:
        with pytest.raises(ValidationError) as exc_req:
            model_cls.model_validate(base)
        assert f"{raw_name} requires exactly one value" in str(exc_req.value)
