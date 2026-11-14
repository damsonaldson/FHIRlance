"""Lazy `_primitive` JSON extension fallback invoked only when Rust validation sees `_` keys."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from fhirlance.base import ExtensionBase, validate_extension_item, validate_primitive_ext_obj


def has_primitive_extension_error(exc: ValidationError) -> bool:
    """Return True if any ValidationError entry is an extra_forbidden `_` key."""
    return any(
        err["type"] == "extra_forbidden"
        and bool(err.get("loc"))
        and isinstance(err["loc"][-1], str)
        and err["loc"][-1].startswith("_")
        for err in exc.errors()
    )


def _unwrap_model_type(annotation: Any) -> type[Any] | None:
    """Extract a FHIRBaseModel subclass from Optional/Annotated/list annotations."""
    if isinstance(annotation, type) and hasattr(annotation, "model_fields"):
        return annotation
    for arg in getattr(annotation, "__args__", ()):
        found = _unwrap_model_type(arg)
        if found is not None:
            return found
    return None


def _validate_primitive_ext_value(value: Any, key: str) -> None:
    if type(value) is list:
        for item in value:
            if item is not None:
                validate_primitive_ext_obj(item, key)
    else:
        validate_primitive_ext_obj(value, key)


def strip_and_validate_primitive_extensions(
    node: Any,
    model_cls: type[Any] | None,
    issues: list[str],
) -> Any:
    """Validate `_primitive` extension elements and strip valid ones before Pydantic re-check."""
    if type(node) is list:
        return [strip_and_validate_primitive_extensions(item, model_cls, issues) for item in node]
    if type(node) is not dict:
        return node

    fields = getattr(model_cls, "model_fields", None) if model_cls is not None else None
    if isinstance(model_cls, type) and issubclass(model_cls, ExtensionBase):
        try:
            validate_extension_item(node)
        except ValueError as exc:
            issues.append(f"Structural[extension]: {exc}")

    out: dict[str, Any] = {}
    for key, value in node.items():
        if key and key[0] == "_" and len(key) > 1 and fields is not None:
            base_name = key[1:]
            if base_name in fields or f"{base_name}_" in fields:
                try:
                    _validate_primitive_ext_value(value, key)
                except ValueError as exc:
                    issues.append(f"Structural[{key}]: {exc}")
                continue
        sub_cls = _unwrap_model_type(fields[key].annotation) if fields and key in fields else None
        out[key] = strip_and_validate_primitive_extensions(value, sub_cls, issues)
    return out
