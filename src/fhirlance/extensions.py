"""First-class FHIR Extension StructureDefinition compiler and validator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from fhirlance import profiles as _profiles
from fhirlance.base import DomainResourceBase, check_value_bounds
from fhirlance.profile_engine import (
    CompiledBindingRule,
    _extract_ref_resource_type,
    pattern_matches,
)
from fhirlance.profiles import COMPLETE_CODE_SYSTEMS, VALUE_SET_SPECS
from fhirlance.terminology import (
    TxOptions,
    _lookup_value_set,
    _normalize_vs_spec,
    parse_tx_options,
    validate_binding_value,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

_TYPE_ALIASES: dict[str, str] = {
    "SimpleQuantity": "Quantity",
    "MoneyQuantity": "Quantity",
}


@dataclass(frozen=True, slots=True)
class ExtensionNodeSpec:
    """Compiled constraints for an Extension root or sub-extension slice."""

    url: str
    min_count: int
    max_count: int | None
    value_forbidden: bool
    value_required: bool
    value_types: frozenset[str]
    allowed_value_keys: frozenset[str]
    value_binding: CompiledBindingRule | None
    value_target_types: frozenset[str]
    has_value_fixed: bool
    value_fixed: Any
    value_pattern: Any
    extension_forbidden: bool
    extension_required: bool
    slicing_closed: bool
    sub_extensions: dict[str, ExtensionNodeSpec]
    value_max_length: int | None = None
    value_min: Any = None
    value_max: Any = None


@dataclass(frozen=True, slots=True)
class CompiledExtension:
    """Compiled Extension StructureDefinition with context, modifier, and value rules."""

    url: str
    is_modifier: bool
    contexts: tuple[tuple[str, str], ...]
    node: ExtensionNodeSpec


@dataclass(frozen=True, slots=True)
class _WalkContext:
    full_path: str
    element_path: str
    type_path: str
    fhir_type: str
    is_root: bool
    is_domain_resource: bool
    parent_type_path: str = ""
    parent_ext_url: str | None = None


@dataclass(frozen=True, slots=True)
class _ValidationEnv:
    compiled_extensions: Mapping[str, CompiledExtension]
    tx_options: TxOptions
    issues: list[str]
    warnings: list[str] | None


def _to_value_key(fhir_type: str) -> str:
    mapped = _TYPE_ALIASES.get(fhir_type, fhir_type)
    return f"value{mapped[0].upper()}{mapped[1:]}" if mapped else ""


def _compile_binding(raw_binding: dict[str, Any] | None, path: str) -> CompiledBindingRule | None:
    if not raw_binding:
        return None
    vs_url = str(raw_binding.get("value_set") or "")
    if not vs_url:
        return None
    raw_vs = raw_binding.get("vs_spec") or _lookup_value_set(vs_url, VALUE_SET_SPECS)
    return CompiledBindingRule(
        path=path,
        parts=(),
        strength=str(raw_binding.get("strength") or "extensible"),
        value_set=vs_url,
        vs_spec=_normalize_vs_spec(raw_vs),
    )


def _compile_node(raw: dict[str, Any], path_prefix: str) -> ExtensionNodeSpec:
    val_types = frozenset(str(t) for t in (raw.get("value_types") or ()) if t)
    allowed_keys = frozenset(_to_value_key(t) for t in val_types if _to_value_key(t))
    sub_compiled = {
        url: _compile_node(sub, f"{path_prefix}.extension:{url}")
        for url, sub in (raw.get("sub_extensions") or {}).items()
    }
    return ExtensionNodeSpec(
        url=str(raw.get("url") or ""),
        min_count=int(raw.get("min") or 0),
        max_count=raw.get("max"),
        value_forbidden=bool(raw.get("value_forbidden")),
        value_required=bool(raw.get("value_required")),
        value_types=val_types,
        allowed_value_keys=allowed_keys,
        value_binding=_compile_binding(raw.get("value_binding"), f"{path_prefix}.value[x]"),
        value_target_types=frozenset(str(t) for t in (raw.get("value_target_types") or ()) if t),
        has_value_fixed=bool(raw.get("has_value_fixed")),
        value_fixed=raw.get("value_fixed"),
        value_pattern=raw.get("value_pattern"),
        extension_forbidden=bool(raw.get("extension_forbidden")),
        extension_required=bool(raw.get("extension_required")),
        slicing_closed=bool(raw.get("slicing_closed")),
        sub_extensions=sub_compiled,
        value_max_length=raw.get("value_max_length"),
        value_min=raw.get("value_min"),
        value_max=raw.get("value_max"),
    )


def compile_extensions(raw: Mapping[str, dict[str, Any]]) -> dict[str, CompiledExtension]:
    """Compile raw Extension StructureDefinition dicts into runtime rules."""
    compiled: dict[str, CompiledExtension] = {}
    for url, spec in raw.items():
        clean_url = str(spec.get("url") or url).split("|", maxsplit=1)[0]
        contexts = tuple(
            (str(c[0]), str(c[1]))
            for c in (spec.get("contexts") or ())
            if len(c) == 2  # noqa: PLR2004
        )
        compiled[url] = CompiledExtension(
            url=clean_url,
            is_modifier=bool(spec.get("is_modifier")),
            contexts=contexts,
            node=_compile_node(spec["node"], f"Extension[{clean_url}]"),
        )
    return compiled


_RAW_BUILTIN_EXTENSIONS: dict[str, dict[str, Any]] = getattr(_profiles, "EXTENSION_CONSTRAINTS", {})
COMPILED_EXTENSIONS: dict[str, CompiledExtension] = compile_extensions(_RAW_BUILTIN_EXTENSIONS)


def _unwrap_model_type(annotation: Any) -> type[Any] | None:
    if isinstance(annotation, type) and hasattr(annotation, "model_fields"):
        return annotation
    for arg in getattr(annotation, "__args__", ()):
        found = _unwrap_model_type(arg)
        if found is not None:
            return found
    return None


def _matches_choice_stem(path: str, stem: str) -> bool:
    if not path.startswith(stem):
        return False
    rest = path[len(stem) :]
    return rest == "" or ("." not in rest and rest[0].isupper())


def _match_element_expr(expr: str, ctx: _WalkContext) -> bool:
    if expr == "Element":
        return not ctx.is_root
    if expr == "Resource":
        return ctx.is_root
    if expr == "DomainResource":
        return ctx.is_root and ctx.is_domain_resource
    if expr == "Extension":
        return ctx.parent_ext_url is not None
    if expr.endswith("[x]"):
        stem = expr[:-3]
        return (
            _matches_choice_stem(ctx.element_path, stem)
            or _matches_choice_stem(ctx.type_path, stem)
            or _matches_choice_stem(ctx.parent_type_path, stem)
        )
    return expr in (ctx.element_path, ctx.type_path, ctx.parent_type_path, ctx.fhir_type)


def _context_matches(contexts: tuple[tuple[str, str], ...], ctx: _WalkContext) -> bool:
    if not contexts:
        return True
    for ctype, expr in contexts:
        if ctype == "element" and _match_element_expr(expr, ctx):
            return True
        if ctype == "extension" and ctx.parent_ext_url is not None:
            if ctx.parent_ext_url == expr.split("|", maxsplit=1)[0]:
                return True
        elif ctype == "fhirpath":
            if any(ch in expr for ch in ("(", ")", "=", " ")):
                return True
            if _match_element_expr(expr, ctx):
                return True
    return False


def _extract_value_items(ext_dict: dict[str, Any]) -> list[tuple[str, Any]]:
    return [
        (k, v)
        for k, v in ext_dict.items()
        if k.startswith("value") and not k.startswith("_") and v is not None
    ]


def _validate_value_binding(
    val: Any,
    ext_path: str,
    binding: CompiledBindingRule,
    env: _ValidationEnv,
) -> None:
    if env.tx_options.mode == "off":
        return
    res = validate_binding_value(
        val,
        ext_path,
        binding.value_set,
        binding.strength,
        env.tx_options,
        profile_prefix="Extension: ",
        vs_spec=binding.vs_spec,
        complete_systems=COMPLETE_CODE_SYSTEMS,
    )
    env.issues.extend(res.errors)
    if env.warnings is not None and res.warnings:
        env.warnings.extend(res.warnings)


def _validate_single_value_item(
    val_key: str,
    val: Any,
    ext_path: str,
    node: ExtensionNodeSpec,
    env: _ValidationEnv,
) -> None:
    if node.allowed_value_keys and val_key not in node.allowed_value_keys:
        allowed = sorted(node.allowed_value_keys)
        env.issues.append(
            f"Extension[{ext_path}]: '{node.url}' requires value[x] type in "
            f"{allowed}, got '{val_key}'"
        )
    if node.has_value_fixed and val != node.value_fixed:
        env.issues.append(
            f"Extension[{ext_path}]: '{val_key}' must equal fixed value {node.value_fixed!r}"
        )
    if node.value_pattern is not None and not pattern_matches(val, node.value_pattern):
        env.issues.append(
            f"Extension[{ext_path}]: '{val_key}' does not match pattern {node.value_pattern!r}"
        )
    if node.value_target_types and val_key == "valueReference" and isinstance(val, dict):
        ref_str = val.get("reference")
        ref_rt = _extract_ref_resource_type(ref_str) if isinstance(ref_str, str) else None
        if ref_rt is not None and ref_rt not in node.value_target_types:
            env.issues.append(
                f"Extension[{ext_path}]: Reference target '{ref_rt}' not in "
                f"{sorted(node.value_target_types)}"
            )
    if node.value_binding is not None:
        _validate_value_binding(val, f"{ext_path}.{val_key}", node.value_binding, env)
    if (
        node.value_max_length is not None
        and isinstance(val, str)
        and len(val) > node.value_max_length
    ):
        env.issues.append(
            f"Extension[{ext_path}]: '{val_key}' length {len(val)} exceeds "
            f"maxLength {node.value_max_length}"
        )
    if node.value_min is not None or node.value_max is not None:
        env.issues.extend(
            check_value_bounds(
                val,
                node.value_min,
                node.value_max,
                f"Extension[{ext_path}]: '{val_key}'",
            )
        )


def _validate_value_constraints(
    ext_dict: dict[str, Any],
    ext_path: str,
    node: ExtensionNodeSpec,
    env: _ValidationEnv,
) -> None:
    val_items = _extract_value_items(ext_dict)
    if node.value_forbidden and val_items:
        env.issues.append(f"Extension[{ext_path}]: value[x] is forbidden (max=0) on '{node.url}'")
        return
    if node.value_required and not val_items:
        prim_val_keys = [k[1:] for k in ext_dict if k.startswith("_value")]
        if not prim_val_keys:
            env.issues.append(
                f"Extension[{ext_path}]: value[x] is required (min=1) on '{node.url}'"
            )
            return
        if node.allowed_value_keys:
            for pv_key in prim_val_keys:
                if pv_key not in node.allowed_value_keys:
                    env.issues.append(
                        f"Extension[{ext_path}]: '{node.url}' requires value[x] type in "
                        f"{sorted(node.allowed_value_keys)}, got '{pv_key}'"
                    )
        return

    for val_key, val in val_items:
        _validate_single_value_item(val_key, val, ext_path, node, env)


def _validate_closed_slices(
    sub_list: list[Any],
    ext_path: str,
    node: ExtensionNodeSpec,
    env: _ValidationEnv,
) -> None:
    for idx, item in enumerate(sub_list):
        if isinstance(item, dict) and item.get("url") not in node.sub_extensions:
            env.issues.append(
                f"Extension[{ext_path}.extension[{idx}]]: unexpected sub-extension "
                f"'{item.get('url')}' in closed slice"
            )


def _group_sub_extensions(sub_list: list[Any]) -> dict[str, list[tuple[int, dict[str, Any]]]]:
    by_url: dict[str, list[tuple[int, dict[str, Any]]]] = {}
    for idx, item in enumerate(sub_list):
        if isinstance(item, dict) and isinstance(item.get("url"), str):
            by_url.setdefault(item["url"], []).append((idx, item))
    return by_url


def _validate_sub_extensions(
    sub_list: list[Any],
    ext_path: str,
    node: ExtensionNodeSpec,
    env: _ValidationEnv,
) -> None:
    if node.extension_forbidden and sub_list:
        env.issues.append(
            f"Extension[{ext_path}]: sub-extensions are forbidden (max=0) on '{node.url}'"
        )
        return
    if node.extension_required and not sub_list:
        env.issues.append(
            f"Extension[{ext_path}]: at least one sub-extension is required on '{node.url}'"
        )
        return
    if not node.sub_extensions:
        return

    by_url = _group_sub_extensions(sub_list)

    for sub_url, sub_spec in node.sub_extensions.items():
        matches = by_url.get(sub_url, [])
        if len(matches) < sub_spec.min_count:
            env.issues.append(
                f"Extension[{ext_path}]: sub-extension '{sub_url}' requires at least "
                f"{sub_spec.min_count} item(s), found {len(matches)}"
            )
        if sub_spec.max_count is not None and len(matches) > sub_spec.max_count:
            env.issues.append(
                f"Extension[{ext_path}]: sub-extension '{sub_url}' allows at most "
                f"{sub_spec.max_count} item(s), found {len(matches)}"
            )
        for idx, item in matches:
            _validate_ext_node(item, f"{ext_path}.extension[{idx}]", sub_spec, env)

    if node.slicing_closed:
        _validate_closed_slices(sub_list, ext_path, node, env)


def _validate_ext_node(
    ext_dict: dict[str, Any],
    ext_path: str,
    node: ExtensionNodeSpec,
    env: _ValidationEnv,
) -> None:
    _validate_value_constraints(ext_dict, ext_path, node, env)
    raw_subs = ext_dict.get("extension")
    sub_list = raw_subs if isinstance(raw_subs, list) else []
    _validate_sub_extensions(sub_list, ext_path, node, env)

    # Also validate any nested full-URL extensions if sub_extensions wasn't sliced
    if sub_list and not node.sub_extensions and not node.extension_forbidden:
        nested_ctx = _WalkContext(
            full_path=f"{ext_path}.extension",
            element_path=f"{ext_path}.extension",
            type_path="Extension",
            fhir_type="Extension",
            is_root=False,
            is_domain_resource=False,
            parent_ext_url=node.url,
        )
        _validate_ext_list(sub_list, f"{ext_path}.extension", False, nested_ctx, env)


def _validate_unknown_ext_children(
    item: dict[str, Any],
    ext_path: str,
    raw_url: str,
    env: _ValidationEnv,
) -> None:
    nested_ctx = _WalkContext(
        full_path=f"{ext_path}.extension",
        element_path=f"{ext_path}.extension",
        type_path="Extension",
        fhir_type="Extension",
        is_root=False,
        is_domain_resource=False,
        parent_ext_url=raw_url,
    )
    if "extension" in item:
        _validate_ext_list(item["extension"], f"{ext_path}.extension", False, nested_ctx, env)
    if "modifierExtension" in item:
        _validate_ext_list(
            item["modifierExtension"], f"{ext_path}.modifierExtension", True, nested_ctx, env
        )


def _validate_ext_list(
    items: Any,
    list_path: str,
    is_modifier_slot: bool,
    ctx: _WalkContext,
    env: _ValidationEnv,
) -> None:
    if not isinstance(items, list):
        return
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        raw_url = item.get("url")
        if not isinstance(raw_url, str) or not raw_url:
            continue
        clean_url = raw_url.split("|", maxsplit=1)[0]
        ext_path = f"{list_path}[{idx}]"
        spec = env.compiled_extensions.get(raw_url) or env.compiled_extensions.get(clean_url)

        if spec is None:
            if is_modifier_slot:
                env.issues.append(
                    f"Extension[{ext_path}]: unknown modifierExtension '{raw_url}' "
                    "cannot be safely ignored"
                )
            else:
                _validate_unknown_ext_children(item, ext_path, raw_url, env)
            continue

        if is_modifier_slot and not spec.is_modifier:
            env.issues.append(
                f"Extension[{ext_path}]: extension '{raw_url}' is not defined as a "
                "modifierExtension (isModifier=false)"
            )
        elif not is_modifier_slot and spec.is_modifier:
            env.issues.append(
                f"Extension[{ext_path}]: modifierExtension '{raw_url}' (isModifier=true) "
                "must appear in 'modifierExtension', not 'extension'"
            )

        if not _context_matches(spec.contexts, ctx):
            allowed = [expr for _, expr in spec.contexts]
            env.issues.append(
                f"Extension[{ext_path}]: extension '{raw_url}' is not valid in context "
                f"'{ctx.full_path}' (allowed: {allowed})"
            )

        _validate_ext_node(item, ext_path, spec.node, env)


def _validate_prim_ext_slot(
    val: Any,
    base_name: str,
    parent_ctx: _WalkContext,
    env: _ValidationEnv,
    idx_suffix: str = "",
) -> None:
    disp_path = f"{parent_ctx.full_path}.{base_name}{idx_suffix}"
    prim_ctx = _WalkContext(
        full_path=disp_path,
        element_path=f"{parent_ctx.element_path}.{base_name}",
        type_path=f"{parent_ctx.type_path}.{base_name}",
        fhir_type="Element",
        is_root=False,
        is_domain_resource=False,
    )
    if isinstance(val, dict):
        if "extension" in val:
            _validate_ext_list(val["extension"], f"{disp_path}.extension", False, prim_ctx, env)
        if "modifierExtension" in val:
            _validate_ext_list(
                val["modifierExtension"], f"{disp_path}.modifierExtension", True, prim_ctx, env
            )
    elif isinstance(val, list):
        for idx, item in enumerate(val):
            if isinstance(item, dict):
                _validate_prim_ext_slot(item, base_name, parent_ctx, env, f"[{idx}]")


def _descend_child(
    key: str,
    val: Any,
    fields: Mapping[str, Any] | None,
    ctx: _WalkContext,
    env: _ValidationEnv,
) -> None:
    sub_cls = _unwrap_model_type(fields[key].annotation) if fields and key in fields else None
    sub_type = sub_cls.__name__ if sub_cls is not None else ""
    parent_type_path = f"{ctx.type_path}.{key}"
    next_type_path = (
        sub_type if sub_type and not sub_type.startswith(ctx.fhir_type) else parent_type_path
    )
    child_ctx = _WalkContext(
        full_path=f"{ctx.full_path}.{key}",
        element_path=f"{ctx.element_path}.{key}",
        type_path=next_type_path,
        fhir_type=sub_type or key,
        is_root=False,
        is_domain_resource=False,
        parent_type_path=parent_type_path,
    )
    _walk_resource_extensions(val, sub_cls, child_ctx, env)


def _walk_resource_extensions(
    node: Any,
    model_cls: type[Any] | None,
    ctx: _WalkContext,
    env: _ValidationEnv,
) -> None:
    if isinstance(node, list):
        for idx, item in enumerate(node):
            item_ctx = _WalkContext(
                full_path=f"{ctx.full_path}[{idx}]",
                element_path=ctx.element_path,
                type_path=ctx.type_path,
                fhir_type=ctx.fhir_type,
                is_root=ctx.is_root,
                is_domain_resource=ctx.is_domain_resource,
                parent_type_path=ctx.parent_type_path,
            )
            _walk_resource_extensions(item, model_cls, item_ctx, env)
        return
    if not isinstance(node, dict):
        return

    if "extension" in node:
        _validate_ext_list(node["extension"], f"{ctx.full_path}.extension", False, ctx, env)
    if "modifierExtension" in node:
        _validate_ext_list(
            node["modifierExtension"], f"{ctx.full_path}.modifierExtension", True, ctx, env
        )

    fields = getattr(model_cls, "model_fields", None) if model_cls is not None else None
    for key, val in node.items():
        if (
            key in ("extension", "modifierExtension", "contained")
            or val is None
            or (key == "resource" and ctx.element_path == "Bundle.entry")
        ):
            continue
        if key.startswith("_") and len(key) > 1:
            _validate_prim_ext_slot(val, key[1:], ctx, env)
            continue
        if isinstance(val, (dict, list)):
            _descend_child(key, val, fields, ctx, env)


def _has_any_extension_key(node: Any) -> bool:
    if type(node) is dict:
        for key, val in node.items():
            if key in ("extension", "modifierExtension") or (key.startswith("_") and len(key) > 1):
                return True
            if isinstance(val, (dict, list)) and _has_any_extension_key(val):
                return True
    elif type(node) is list:
        for item in node:
            if isinstance(item, (dict, list)) and _has_any_extension_key(item):
                return True
    return False


def validate_extensions(
    resource: dict[str, Any],
    model_cls: type[Any],
    rtype: str,
    *,
    compiled_extensions: Mapping[str, CompiledExtension] = COMPILED_EXTENSIONS,
    tx: TxOptions | str = "local",
    _warnings_out: list[str] | None = None,
    _skip_precheck: bool = False,
) -> list[str]:
    """Validate all extensions and modifierExtensions in a FHIR resource."""
    if not _skip_precheck and not _has_any_extension_key(resource):
        return []
    tx_options = tx if isinstance(tx, TxOptions) else parse_tx_options(tx)
    issues: list[str] = []
    env = _ValidationEnv(
        compiled_extensions=compiled_extensions,
        tx_options=tx_options,
        issues=issues,
        warnings=_warnings_out,
    )
    root_ctx = _WalkContext(
        full_path=rtype,
        element_path=rtype,
        type_path=rtype,
        fhir_type=rtype,
        is_root=True,
        is_domain_resource=issubclass(model_cls, DomainResourceBase),
    )
    _walk_resource_extensions(resource, model_cls, root_ctx, env)
    return issues
