"""Audit severity levels and default severity by action."""

from __future__ import annotations

import enum


class AuditSeverity(str, enum.Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# Meaningful-event defaults. Unlisted actions are INFO.
ACTION_SEVERITY: dict[str, AuditSeverity] = {
    "auth.login_failed": AuditSeverity.WARNING,
    "auth.account_locked": AuditSeverity.CRITICAL,
    "auth.account_disabled": AuditSeverity.CRITICAL,
    "org.delete": AuditSeverity.WARNING,
    "org.archive": AuditSeverity.WARNING,
    "org.member_remove": AuditSeverity.WARNING,
    "org.config_changed": AuditSeverity.WARNING,
    "scan.failed": AuditSeverity.WARNING,
    "scan.plugin_failed": AuditSeverity.ERROR,
    "scan.cancel": AuditSeverity.WARNING,
    "monitoring.alert_opened": AuditSeverity.WARNING,
    "admin.api_key_revoked": AuditSeverity.WARNING,
}


def normalize_severity(value: str | AuditSeverity | None) -> str:
    if value is None:
        return AuditSeverity.INFO.value
    raw = value.value if isinstance(value, AuditSeverity) else str(value).strip().lower()
    try:
        return AuditSeverity(raw).value
    except ValueError:
        return AuditSeverity.INFO.value


def severity_for_action(action: str, override: str | AuditSeverity | None = None) -> str:
    if override is not None:
        return normalize_severity(override)
    mapped = ACTION_SEVERITY.get(action)
    if mapped is None:
        return AuditSeverity.INFO.value
    return mapped.value
