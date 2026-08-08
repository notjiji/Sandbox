"""Declarative condition evaluation for scanner rules."""

from __future__ import annotations

from typing import Any

# Maps RFC header names to boolean fields on HttpHeadersParsedData
HEADER_TO_PATH: dict[str, str] = {
    "content-security-policy": "has_csp",
    "strict-transport-security": "has_hsts",
    "referrer-policy": "has_referrer_policy",
    "x-frame-options": "has_x_frame_options",
    "x-content-type-options": "has_x_content_type_options",
    "permissions-policy": "has_permissions_policy",
    "feature-policy": "has_permissions_policy",
}


def _get_path(context: dict[str, Any], path: str) -> Any:
    current: Any = context
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
    return current


def _normalize_header_name(header_name: str) -> str:
    return header_name.strip().lower()


def _evaluate_shorthand(key: str, value: Any, context: dict[str, Any]) -> bool:
    if key == "header_missing":
        header_name = _normalize_header_name(str(value))
        mapped_path = HEADER_TO_PATH.get(header_name)
        if mapped_path is not None:
            return not bool(_get_path(context, mapped_path))
        headers = context.get("headers") or {}
        if isinstance(headers, dict):
            return not any(k.lower() == header_name for k in headers)
        return True

    if key == "header_present":
        header_name = _normalize_header_name(str(value))
        mapped_path = HEADER_TO_PATH.get(header_name)
        if mapped_path is not None:
            return bool(_get_path(context, mapped_path))
        headers = context.get("headers") or {}
        if isinstance(headers, dict):
            return any(k.lower() == header_name for k in headers)
        return False

    if key == "path":
        return bool(_get_path(context, str(value)))

    if key == "path_missing":
        return not bool(_get_path(context, str(value)))

    if key == "path_truthy":
        return bool(_get_path(context, str(value)))

    if key == "path_falsy":
        return not bool(_get_path(context, str(value)))

    if key == "path_eq":
        if not isinstance(value, dict) or "path" not in value:
            return False
        return _get_path(context, str(value["path"])) == value.get("value")

    if key == "path_nonempty":
        target = _get_path(context, str(value))
        if target is None:
            return False
        if isinstance(target, (list, dict, str)):
            return len(target) > 0
        return bool(target)

    if key == "path_contains":
        if not isinstance(value, dict) or "path" not in value:
            return False
        target = _get_path(context, str(value["path"]))
        needle = value.get("value")
        if isinstance(target, (list, tuple, set)):
            return needle in target
        if isinstance(target, str) and isinstance(needle, str):
            return needle in target
        return False

    if key == "port_open":
        open_ports = context.get("open_ports") or []
        try:
            return int(value) in open_ports
        except (TypeError, ValueError):
            return False

    if key == "cors_wildcard":
        origin = _get_path(context, "access_control_allow_origin")
        if not isinstance(origin, str):
            return False
        return origin.strip() == "*"

    return False


def evaluate_condition(condition: dict[str, Any] | None, context: dict[str, Any]) -> bool:
    if not condition:
        return False

    if "op" in condition:
        op = condition["op"]
        if op == "and":
            return all(evaluate_condition(item, context) for item in condition.get("conditions", []))
        if op == "or":
            return any(evaluate_condition(item, context) for item in condition.get("conditions", []))
        if op == "not":
            inner = condition.get("condition")
            return not evaluate_condition(inner, context) if inner else True
        if op == "eq":
            return _get_path(context, str(condition["path"])) == condition.get("value")
        if op == "neq":
            return _get_path(context, str(condition["path"])) != condition.get("value")
        if op == "truthy":
            return bool(_get_path(context, str(condition["path"])))
        if op == "falsy":
            return not bool(_get_path(context, str(condition["path"])))
        if op == "nonempty":
            target = _get_path(context, str(condition["path"]))
            if target is None:
                return False
            if isinstance(target, (list, dict, str)):
                return len(target) > 0
            return bool(target)
        if op == "empty":
            target = _get_path(context, str(condition["path"]))
            if target is None:
                return True
            if isinstance(target, (list, dict, str)):
                return len(target) == 0
            return not bool(target)
        if op == "lt":
            target = _get_path(context, str(condition["path"]))
            limit = condition.get("value")
            try:
                return target is not None and target < limit
            except TypeError:
                return False
        if op == "lte":
            target = _get_path(context, str(condition["path"]))
            limit = condition.get("value")
            try:
                return target is not None and target <= limit
            except TypeError:
                return False
        if op == "gt":
            target = _get_path(context, str(condition["path"]))
            limit = condition.get("value")
            try:
                return target is not None and target > limit
            except TypeError:
                return False
        if op == "contains":
            target = _get_path(context, str(condition["path"]))
            needle = condition.get("value")
            if isinstance(target, (list, tuple, set)):
                return needle in target
            if isinstance(target, str) and isinstance(needle, str):
                return needle in target
            return False
        return False

    if len(condition) == 1:
        key, value = next(iter(condition.items()))
        return _evaluate_shorthand(key, value, context)

    return all(_evaluate_shorthand(key, value, context) for key, value in condition.items())


def matches(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    """Return True when the rule condition matches the evaluation context."""
    return evaluate_condition(condition, context)
