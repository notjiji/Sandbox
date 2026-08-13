"""Sync monitoring alert candidates into Phase 6 findings for the shared risk engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.risk_engine.scoring import points_for_severity
from app.findings.constants import (
    CATEGORY_SERVER_CAPACITY,
    CATEGORY_SERVER_MAINTENANCE,
    CATEGORY_SERVER_SECURITY,
    FINDING_SOURCE_MONITORING,
    MONITORING_PLUGIN,
)
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.repositories.finding_repository import upsert_monitoring_finding
from app.monitoring.enums import AlertSeverity
from app.monitoring.services.alert_engine import AlertCandidate
from app.risk.repositories.risk_repository import get_recommendation_by_code, get_rule_for_finding

_ALERT_TO_FINDING_SEVERITY = {
    AlertSeverity.CRITICAL: FindingSeverity.CRITICAL,
    AlertSeverity.HIGH: FindingSeverity.HIGH,
    AlertSeverity.MEDIUM: FindingSeverity.MEDIUM,
    AlertSeverity.LOW: FindingSeverity.LOW,
    AlertSeverity.INFO: FindingSeverity.INFO,
}


def _category_for_code(code: str) -> str:
    if code.startswith(("SSH_", "FIREWALL_", "FAIL2BAN_", "SECURITY_UPDATES")):
        return CATEGORY_SERVER_SECURITY
    if code.startswith(("CPU_", "RAM_", "DISK_")):
        return CATEGORY_SERVER_CAPACITY
    return CATEGORY_SERVER_MAINTENANCE


def _extract_recommendation(message: str | None) -> str | None:
    if not message:
        return None
    if "Recommendation:" in message:
        return message.split("Recommendation:", 1)[1].strip()
    return message


def _description_from_message(message: str | None) -> str | None:
    if not message:
        return None
    if "Recommendation:" in message:
        current = message.split("Recommendation:", 1)[0].strip()
        return current or None
    return message


def _disk_prefix_severity(code: str) -> FindingSeverity | None:
    if code.startswith("DISK_CRITICAL__"):
        return FindingSeverity.CRITICAL
    if code.startswith("DISK_HIGH__"):
        return FindingSeverity.HIGH
    if code.startswith("DISK_WARN__"):
        return FindingSeverity.MEDIUM
    return None


def _resolve_monitoring_finding_fields(
    db: Session,
    *,
    candidate: AlertCandidate,
) -> tuple[FindingSeverity, float, str | None, str | None]:
    rule = get_rule_for_finding(db, plugin=MONITORING_PLUGIN, finding_code=candidate.code)
    if rule:
        recommendation = None
        if rule.recommendation_id:
            rec = get_recommendation_by_code(db, code=rule.recommendation_id)
            recommendation = rec.text if rec else None
        return (
            rule.severity,
            float(rule.score),
            recommendation,
            rule.recommendation_id,
        )

    disk_severity = _disk_prefix_severity(candidate.code)
    if disk_severity is not None:
        return disk_severity, points_for_severity(disk_severity), None, None

    severity = _ALERT_TO_FINDING_SEVERITY.get(candidate.severity, FindingSeverity.MEDIUM)
    return severity, points_for_severity(severity), _extract_recommendation(candidate.message), None


def sync_monitoring_findings(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    candidates: list[AlertCandidate],
    active_codes: set[str],
    now: datetime | None = None,
) -> bool:
    """Upsert open monitoring findings and resolve cleared ones. Returns True if risk should refresh."""
    timestamp = now or datetime.now(UTC)
    risk_dirty = False

    for candidate in candidates:
        severity, risk_score, recommendation, recommendation_id = _resolve_monitoring_finding_fields(
            db, candidate=candidate
        )
        _, changed = upsert_monitoring_finding(
            db,
            project_id=project_id,
            asset_id=asset_id,
            finding_code=candidate.code,
            title=candidate.title,
            description=_description_from_message(candidate.message),
            severity=severity,
            risk_score=risk_score,
            evidence=candidate.evidence,
            recommendation=recommendation or _extract_recommendation(candidate.message),
            recommendation_id=recommendation_id,
            category=_category_for_code(candidate.code),
            detected_at=timestamp,
        )
        if changed:
            risk_dirty = True

    open_findings = (
        db.query(Finding)
        .filter(
            Finding.asset_id == asset_id,
            Finding.source == FINDING_SOURCE_MONITORING,
            Finding.status == FindingStatus.OPEN,
        )
        .all()
    )
    for finding in open_findings:
        if finding.finding_code and finding.finding_code not in active_codes:
            finding.status = FindingStatus.RESOLVED
            finding.resolved_at = timestamp
            db.add(finding)
            risk_dirty = True

    if risk_dirty:
        db.flush()
    return risk_dirty
