"""Canonical event names. Accepts `asset.create` or `ASSET_CREATED`."""

from __future__ import annotations

from app.audit.events import AuditAction

_PAST_TO_VERB = {
    "created": "create",
    "updated": "update",
    "deleted": "delete",
    "archived": "archive",
    "restored": "restore",
    "cancelled": "cancel",
    "canceled": "cancel",
    "generated": "generate",
    "downloaded": "download",
    "requested": "request",
    "invited": "invite",
    "removed": "remove",
    "changed": "change",
}

_AUDIT_BY_ATTR = {
    name: value
    for name, value in vars(AuditAction).items()
    if name.isupper() and isinstance(value, str)
}
_AUDIT_BY_VALUE = {value.lower(): value for value in _AUDIT_BY_ATTR.values()}


def normalize_action(action: str | None) -> str | None:
    if action is None:
        return None
    text = action.strip()
    if not text:
        return text
    lowered = text.lower()
    if lowered in _AUDIT_BY_VALUE:
        return _AUDIT_BY_VALUE[lowered]
    if "." in text:
        return lowered
    key = text.upper().replace("-", "_")
    mapped = _AUDIT_BY_ATTR.get(key)
    if mapped:
        return mapped
    if key.endswith("_CREATED"):
        mapped = _AUDIT_BY_ATTR.get(key[:-1])  # CREATED → CREATE
        if mapped:
            return mapped
    if "_" not in key:
        return lowered
    domain, rest = key.split("_", 1)
    verb = _PAST_TO_VERB.get(rest.lower(), rest.lower())
    candidate = f"{domain.lower()}.{verb}"
    return _AUDIT_BY_VALUE.get(candidate, candidate)
