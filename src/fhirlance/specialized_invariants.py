"""Specialized FHIR R4 resource invariants and Subscription semantic checks."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

_MAX_ITEM_DEPTH = 64
_QUE_12_MIN_ENABLE_WHEN = 2

_QUE_5_ALLOWED_TYPES = frozenset(
    {
        "choice",
        "open-choice",
        "decimal",
        "integer",
        "date",
        "dateTime",
        "time",
        "string",
        "quantity",
    }
)
_QUE_10_ALLOWED_TYPES = frozenset(
    {
        "boolean",
        "decimal",
        "integer",
        "string",
        "text",
        "url",
        "open-choice",
    }
)

_TST_OP_EXEMPT_TYPES = frozenset({"capabilities", "search", "transaction", "history"})
_TST_ASSERT_FIELDS = (
    "contentType",
    "expression",
    "headerField",
    "minimumId",
    "navigationLinks",
    "path",
    "requestMethod",
    "resource",
    "responseCode",
    "response",
    "validateProfileId",
)

_MSQ_VALID_COORD_SYSTEMS = frozenset({0, 1})
_MSQ_REFSEQ_FIELDS = (
    "genomeBuild",
    "referenceSeqId",
    "referenceSeqPointer",
    "referenceSeqString",
)

_BACKPORT_TOPIC_CANONICAL_URL = (
    "http://hl7.org/fhir/uv/subscriptions-backport/StructureDefinition/backport-topic-canonical"
)
_BACKPORT_PAYLOAD_CONTENT_URL = (
    "http://hl7.org/fhir/uv/subscriptions-backport/StructureDefinition/backport-payload-content"
)
_SUB_PAYLOAD_CONTENT_CODES = frozenset({"empty", "id-only", "full-resource"})


def _is_present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def _count(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, list):
        return len(value)
    if isinstance(value, dict):
        return 1 if value else 0
    return 1


def _field_count(obj: dict[str, Any], fields: tuple[str, ...]) -> int:
    return sum(_count(obj.get(field)) for field in fields)


def _check_questionnaire_item_types(item: dict[str, Any], path: str) -> list[str]:
    issues: list[str] = []
    item_type = item.get("type")
    has_nested = _is_present(item.get("item"))

    if item_type == "group" and not has_nested:
        issues.append(f"Invariant[que-1] {path}: group item must have nested items")
    if item_type == "display":
        if has_nested:
            issues.append(f"Invariant[que-1] {path}: display item cannot have nested items")
        if _is_present(item.get("code")):
            issues.append(f"Invariant[que-3] {path}: display item cannot have a code")
        if _is_present(item.get("required")) or _is_present(item.get("repeats")):
            issues.append(f"Invariant[que-6] {path}: display item cannot have required or repeats")
        if _is_present(item.get("readOnly")):
            issues.append(f"Invariant[que-9] {path}: display item cannot have readOnly")

    if item_type in ("group", "display") and _is_present(item.get("initial")):
        issues.append(f"Invariant[que-8] {path}: group or display item cannot have initial values")
    return issues


def _check_questionnaire_item_options(item: dict[str, Any], path: str) -> list[str]:
    issues: list[str] = []
    item_type = item.get("type")
    has_opt = _is_present(item.get("answerOption"))
    has_vs = _is_present(item.get("answerValueSet"))
    has_init = _is_present(item.get("initial"))

    if has_opt and has_vs:
        issues.append(f"Invariant[que-4] {path}: cannot have both answerOption and answerValueSet")
    if item_type not in _QUE_5_ALLOWED_TYPES and (has_opt or has_vs):
        issues.append(
            f"Invariant[que-5] {path}: item type '{item_type}' cannot have answerOption/ValueSet"
        )
    if item_type not in _QUE_10_ALLOWED_TYPES and _is_present(item.get("maxLength")):
        issues.append(
            f"Invariant[que-10] {path}: maxLength not allowed for item type '{item_type}'"
        )
    if has_opt and has_init:
        issues.append(f"Invariant[que-11] {path}: answerOption and initial cannot both be present")
    return issues


def _check_questionnaire_item_logic(item: dict[str, Any], path: str) -> list[str]:
    issues: list[str] = []
    enable_when = item.get("enableWhen")
    if _count(enable_when) > _QUE_12_MIN_ENABLE_WHEN and not _is_present(
        item.get("enableBehavior")
    ):
        issues.append(
            f"Invariant[que-12] {path}: enableBehavior required when enableWhen.count() > 2"
        )

    if item.get("repeats") is not True and _count(item.get("initial")) > 1:
        issues.append(
            f"Invariant[que-13] {path}: multiple initial values only allowed when repeats=true"
        )

    if isinstance(enable_when, list):
        for idx, ew in enumerate(enable_when):
            if (
                isinstance(ew, dict)
                and ew.get("operator") == "exists"
                and not isinstance(ew.get("answerBoolean"), bool)
            ):
                issues.append(
                    f"Invariant[que-7] {path}.enableWhen[{idx}]: "
                    "operator 'exists' requires answerBoolean"
                )
    return issues


def _push_indexed_dicts(
    stack: list[tuple[dict[str, Any], str, int]],
    items: Any,
    prefix: str,
    depth: int,
) -> None:
    if not isinstance(items, list) or depth > _MAX_ITEM_DEPTH:
        return
    for idx in range(len(items) - 1, -1, -1):
        child = items[idx]
        if isinstance(child, dict):
            stack.append((child, f"{prefix}[{idx}]", depth))


def _check_questionnaire_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    seen_link_ids: set[str] = set()
    stack: list[tuple[dict[str, Any], str, int]] = []
    _push_indexed_dicts(stack, resource.get("item"), "item", 1)

    while stack:
        item, path, depth = stack.pop()
        link_id = item.get("linkId")
        if isinstance(link_id, str):
            if link_id in seen_link_ids:
                issues.append(f"Invariant[que-2] {path}: duplicate linkId '{link_id}'")
            seen_link_ids.add(link_id)

        issues.extend(_check_questionnaire_item_types(item, path))
        issues.extend(_check_questionnaire_item_options(item, path))
        issues.extend(_check_questionnaire_item_logic(item, path))
        _push_indexed_dicts(stack, item.get("item"), f"{path}.item", depth + 1)

    return issues


def _check_questionnaire_response_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    stack: list[tuple[dict[str, Any], str, int]] = []
    _push_indexed_dicts(stack, resource.get("item"), "item", 1)

    while stack:
        item, path, depth = stack.pop()
        if _is_present(item.get("answer")) and _is_present(item.get("item")):
            issues.append(
                f"Invariant[qrs-1] {path}: nested item cannot be beneath both item and answer"
            )

        answers = item.get("answer")
        if isinstance(answers, list):
            for a_idx in range(len(answers) - 1, -1, -1):
                ans = answers[a_idx]
                if isinstance(ans, dict):
                    _push_indexed_dicts(
                        stack, ans.get("item"), f"{path}.answer[{a_idx}].item", depth + 1
                    )

        _push_indexed_dicts(stack, item.get("item"), f"{path}.item", depth + 1)

    return issues


def _check_capability_kind_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    kind = resource.get("kind")
    has_impl = _is_present(resource.get("implementation"))
    has_sw = _is_present(resource.get("software"))

    if kind == "instance" and not has_impl:
        issues.append("Invariant[cpb-14]: kind='instance' requires implementation")
    elif kind == "capability" and (has_impl or not has_sw):
        issues.append(
            "Invariant[cpb-15]: kind='capability' requires software and forbids implementation"
        )
    elif kind == "requirements" and (has_impl or has_sw):
        issues.append("Invariant[cpb-16]: kind='requirements' forbids implementation and software")
    return issues


def _check_capability_resource(
    res: dict[str, Any],
    path: str,
    seen_types: set[str],
) -> list[str]:
    issues: list[str] = []
    res_type = res.get("type")
    if isinstance(res_type, str):
        if res_type in seen_types:
            issues.append(f"Invariant[cpb-9] {path}: duplicate resource type '{res_type}'")
        seen_types.add(res_type)

    seen_sp: set[str] = set()
    for sp_idx, sp in enumerate(res.get("searchParam") or []):
        if not isinstance(sp, dict):
            continue
        sp_name = sp.get("name")
        if isinstance(sp_name, str):
            if sp_name in seen_sp:
                issues.append(
                    f"Invariant[cpb-12] {path}.searchParam[{sp_idx}]: "
                    f"duplicate searchParam name '{sp_name}'"
                )
            seen_sp.add(sp_name)
    return issues


def _check_capability_rest_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for r_idx, rest in enumerate(resource.get("rest") or []):
        if not isinstance(rest, dict):
            continue
        seen_types: set[str] = set()
        for res_idx, res in enumerate(rest.get("resource") or []):
            if isinstance(res, dict):
                issues.extend(
                    _check_capability_resource(
                        res, f"rest[{r_idx}].resource[{res_idx}]", seen_types
                    )
                )
    return issues


def _check_capability_statement_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if (
        not _is_present(resource.get("rest"))
        and not _is_present(resource.get("messaging"))
        and not _is_present(resource.get("document"))
    ):
        issues.append("Invariant[cpb-1]: must have at least one of rest, messaging, or document")

    if (
        not _is_present(resource.get("description"))
        and not _is_present(resource.get("software"))
        and not _is_present(resource.get("implementation"))
    ):
        issues.append(
            "Invariant[cpb-2]: must have at least one of description, software, or implementation"
        )

    kind = resource.get("kind")
    for idx, msg in enumerate(resource.get("messaging") or []):
        if isinstance(msg, dict) and _is_present(msg.get("endpoint")) and kind != "instance":
            issues.append(
                f"Invariant[cpb-3] messaging[{idx}]: endpoint only allowed when kind='instance'"
            )

    seen_docs: set[tuple[str | None, str | None]] = set()
    for idx, doc in enumerate(resource.get("document") or []):
        if not isinstance(doc, dict):
            continue
        profile = doc.get("profile")
        mode = doc.get("mode")
        key = (
            profile if isinstance(profile, str) else None,
            mode if isinstance(mode, str) else None,
        )
        if key in seen_docs:
            issues.append(f"Invariant[cpb-7] document[{idx}]: duplicate document (profile, mode)")
        seen_docs.add(key)

    issues.extend(_check_capability_kind_invariants(resource))
    issues.extend(_check_capability_rest_invariants(resource))
    return issues


def _check_operation_definition_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    stack: list[tuple[dict[str, Any], str, int]] = []
    _push_indexed_dicts(stack, resource.get("parameter"), "parameter", 1)

    while stack:
        param, path, depth = stack.pop()
        ptype = param.get("type")
        if not _is_present(ptype) and not _is_present(param.get("part")):
            issues.append(f"Invariant[opd-1] {path}: parameter must have type or part")
        if _is_present(param.get("searchType")) and ptype != "string":
            issues.append(f"Invariant[opd-2] {path}: searchType only allowed when type='string'")
        if _is_present(param.get("targetProfile")) and ptype not in ("Reference", "canonical"):
            issues.append(
                f"Invariant[opd-3] {path}: targetProfile only allowed for Reference or canonical"
            )
        _push_indexed_dicts(stack, param.get("part"), f"{path}.part", depth + 1)

    return issues


def _check_search_parameter_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if _is_present(resource.get("xpath")) and not _is_present(resource.get("xpathUsage")):
        issues.append("Invariant[spd-1]: xpathUsage required when xpath is present")
    if _is_present(resource.get("chain")) and resource.get("type") != "reference":
        issues.append("Invariant[spd-2]: chain only allowed when type='reference'")
    return issues


def _check_concept_map_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for g_idx, group in enumerate(resource.get("group") or []):
        if not isinstance(group, dict):
            continue
        for e_idx, elem in enumerate(group.get("element") or []):
            if not isinstance(elem, dict):
                continue
            for t_idx, target in enumerate(elem.get("target") or []):
                if (
                    isinstance(target, dict)
                    and target.get("equivalence") in ("narrower", "inexact")
                    and not _is_present(target.get("comment"))
                ):
                    issues.append(
                        f"Invariant[cmd-1] group[{g_idx}].element[{e_idx}].target[{t_idx}]: "
                        "comment required for narrower or inexact equivalence"
                    )

        unmapped = group.get("unmapped")
        if isinstance(unmapped, dict):
            mode = unmapped.get("mode")
            if mode == "fixed" and not _is_present(unmapped.get("code")):
                issues.append(
                    f"Invariant[cmd-2] group[{g_idx}].unmapped: code required when mode='fixed'"
                )
            if mode == "other-map" and not _is_present(unmapped.get("url")):
                issues.append(
                    f"Invariant[cmd-3] group[{g_idx}].unmapped: url required when mode='other-map'"
                )
    return issues


def _check_testscript_operation(op: dict[str, Any], path: str, key: str) -> list[str]:
    has_source = _is_present(op.get("sourceId"))
    other_count = _field_count(op, ("targetId", "url", "params"))
    op_type = op.get("type")
    type_code = op_type.get("code") if isinstance(op_type, dict) else None
    if has_source or other_count == 1 or type_code in _TST_OP_EXEMPT_TYPES:
        return []
    return [
        f"Invariant[{key}] {path}: operation must specify sourceId, "
        "one of targetId/url/params, or an exempt type"
    ]


def _check_testscript_assert(
    asrt: dict[str, Any],
    path: str,
    keys: tuple[str, str, str],
) -> list[str]:
    issues: list[str] = []
    k_single, k_compare, k_direction = keys

    if not _is_present(asrt.get("extension")) and _field_count(asrt, _TST_ASSERT_FIELDS) > 1:
        issues.append(f"Invariant[{k_single}] {path}: only a single assertion allowed in assert")

    has_cmp_id = _is_present(asrt.get("compareToSourceId"))
    has_cmp_target = _is_present(asrt.get("compareToSourceExpression")) or _is_present(
        asrt.get("compareToSourcePath")
    )
    if has_cmp_id != has_cmp_target:
        issues.append(
            f"Invariant[{k_compare}] {path}: compareToSourceId must be paired with "
            "compareToSourceExpression or compareToSourcePath"
        )

    direction = asrt.get("direction")
    if _is_present(direction) and direction != "response":
        has_resp = _is_present(asrt.get("response")) or _is_present(asrt.get("responseCode"))
        if direction != "request" or has_resp:
            issues.append(
                f"Invariant[{k_direction}] {path}: "
                "response and responseCode must be empty when direction='request'"
            )
    return issues


def _check_testscript_actions(
    actions: Any,
    prefix: str,
    action_key: str,
    op_key: str,
    assert_keys: tuple[str, str, str] | None,
) -> list[str]:
    issues: list[str] = []
    if not isinstance(actions, list):
        return issues
    for idx, action in enumerate(actions):
        if not isinstance(action, dict):
            continue
        path = f"{prefix}[{idx}]"
        op = action.get("operation")
        asrt = action.get("assert")
        has_op = _is_present(op)
        has_asrt = _is_present(asrt)
        if action_key and has_op == has_asrt:
            issues.append(
                f"Invariant[{action_key}] {path}: must contain either operation or assert"
            )
        if isinstance(op, dict):
            issues.extend(_check_testscript_operation(op, f"{path}.operation", op_key))
        if assert_keys is not None and isinstance(asrt, dict):
            issues.extend(_check_testscript_assert(asrt, f"{path}.assert", assert_keys))
    return issues


def _check_testscript_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    metadata = resource.get("metadata")
    if isinstance(metadata, dict):
        caps = metadata.get("capability")
        if isinstance(caps, list) and not any(
            isinstance(c, dict) and (c.get("required") is True or c.get("validated") is True)
            for c in caps
        ):
            issues.append(
                "Invariant[tst-4] metadata: capability must contain required or validated"
            )

    for idx, var in enumerate(resource.get("variable") or []):
        if isinstance(var, dict) and all(
            _is_present(var.get(field)) for field in ("expression", "headerField", "path")
        ):
            issues.append(
                f"Invariant[tst-3] variable[{idx}]: "
                "cannot contain all of expression, headerField, and path"
            )

    setup = resource.get("setup")
    if isinstance(setup, dict):
        issues.extend(
            _check_testscript_actions(
                setup.get("action"),
                "setup.action",
                "tst-1",
                "tst-7",
                ("tst-5", "tst-10", "tst-12"),
            )
        )

    for idx, test in enumerate(resource.get("test") or []):
        if isinstance(test, dict):
            issues.extend(
                _check_testscript_actions(
                    test.get("action"),
                    f"test[{idx}].action",
                    "tst-2",
                    "tst-8",
                    ("tst-6", "tst-11", "tst-13"),
                )
            )

    teardown = resource.get("teardown")
    if isinstance(teardown, dict):
        issues.extend(
            _check_testscript_actions(
                teardown.get("action"),
                "teardown.action",
                "",
                "tst-9",
                None,
            )
        )
    return issues


def _check_structure_map_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    stack: list[tuple[dict[str, Any], str, int]] = []
    groups = resource.get("group")
    if isinstance(groups, list):
        for g_idx in range(len(groups) - 1, -1, -1):
            group = groups[g_idx]
            if isinstance(group, dict):
                _push_indexed_dicts(stack, group.get("rule"), f"group[{g_idx}].rule", 1)

    while stack:
        rule, path, depth = stack.pop()
        for t_idx, target in enumerate(rule.get("target") or []):
            if not isinstance(target, dict):
                continue
            has_context = _is_present(target.get("context"))
            if _is_present(target.get("element")) and not has_context:
                issues.append(f"Invariant[smp-1] {path}.target[{t_idx}]: element requires context")
            if has_context and not _is_present(target.get("contextType")):
                issues.append(
                    f"Invariant[smp-2] {path}.target[{t_idx}]: context requires contextType"
                )
        _push_indexed_dicts(stack, rule.get("rule"), f"{path}.rule", depth + 1)

    return issues


def _check_molecular_sequence_invariants(resource: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    coord = resource.get("coordinateSystem")
    if coord is not None and (isinstance(coord, bool) or coord not in _MSQ_VALID_COORD_SYSTEMS):
        issues.append("Invariant[msq-3]: coordinateSystem must be 0 or 1")

    ref_seq = resource.get("referenceSeq")
    if isinstance(ref_seq, dict):
        has_chrom = _is_present(ref_seq.get("chromosome"))
        has_gb = _is_present(ref_seq.get("genomeBuild"))
        if has_chrom != has_gb:
            issues.append(
                "Invariant[msq-5] referenceSeq: "
                "chromosome and genomeBuild must both be present or both absent"
            )
        if _field_count(ref_seq, _MSQ_REFSEQ_FIELDS) != 1:
            issues.append(
                "Invariant[msq-6] referenceSeq: must have exactly one of "
                "genomeBuild, referenceSeqId, referenceSeqPointer, or referenceSeqString"
            )
    return issues


def _check_subscription_backport_extensions(extensions: Any, path: str) -> list[str]:
    issues: list[str] = []
    if not isinstance(extensions, list):
        return issues
    for idx, ext in enumerate(extensions):
        if not isinstance(ext, dict):
            continue
        url = ext.get("url")
        if url == _BACKPORT_TOPIC_CANONICAL_URL:
            val = ext.get("valueCanonical") or ext.get("valueUri")
            if not isinstance(val, str) or not val.strip():
                issues.append(
                    f"Subscription[{path}.extension[{idx}]]: "
                    "backport-topic-canonical requires non-empty valueCanonical or valueUri"
                )
        elif url == _BACKPORT_PAYLOAD_CONTENT_URL:
            code = ext.get("valueCode")
            if code not in _SUB_PAYLOAD_CONTENT_CODES:
                issues.append(
                    f"Subscription[{path}.extension[{idx}]]: "
                    "backport-payload-content valueCode must be empty, id-only, or full-resource"
                )
    return issues


def _check_subscription_invariants(resource: dict[str, Any]) -> list[str]:
    issues = _check_subscription_backport_extensions(resource.get("extension"), "Subscription")
    channel = resource.get("channel")
    if not isinstance(channel, dict):
        return issues

    ch_type = channel.get("type")
    endpoint = channel.get("endpoint")
    if isinstance(endpoint, str):
        if ch_type == "rest-hook" and not endpoint.startswith(("http://", "https://")):
            issues.append(
                "Subscription[channel.endpoint]: "
                "rest-hook endpoint must start with http:// or https://"
            )
        elif ch_type == "email" and "@" not in endpoint and not endpoint.startswith("mailto:"):
            issues.append(
                "Subscription[channel.endpoint]: "
                "email endpoint must contain '@' or start with 'mailto:'"
            )

    issues.extend(_check_subscription_backport_extensions(channel.get("extension"), "channel"))
    return issues


SPECIALIZED_INVARIANT_CHECKS: dict[str, Callable[[dict[str, Any]], list[str]]] = {
    "Questionnaire": _check_questionnaire_invariants,
    "QuestionnaireResponse": _check_questionnaire_response_invariants,
    "CapabilityStatement": _check_capability_statement_invariants,
    "OperationDefinition": _check_operation_definition_invariants,
    "SearchParameter": _check_search_parameter_invariants,
    "ConceptMap": _check_concept_map_invariants,
    "TestScript": _check_testscript_invariants,
    "StructureMap": _check_structure_map_invariants,
    "MolecularSequence": _check_molecular_sequence_invariants,
    "Subscription": _check_subscription_invariants,
}
