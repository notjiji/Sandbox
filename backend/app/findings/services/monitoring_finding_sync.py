"""Sync monitoring security conditions into Phase 6 findings for the shared risk engine."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.risk_engine.scoring import points_for_severity
from app.findings.constants import FINDING_SOURCE_MONITORING, MONITORING_PLUGIN
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.repositories.finding_repository import upsert_monitoring_finding
from app.monitoring.services.finding_engine import FindingCandidate
from app.risk.repositories.risk_repository import get_recommendation_by_code, get_rule_for_finding


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


def _resolve_monitoring_finding_fields(
    db: Session,
    *,
    candidate: FindingCandidate,
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
    return (
        candidate.severity,
        points_for_severity(candidate.severity),
        _extract_recommendation(candidate.message),
        None,
    )


def sync_monitoring_findings(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    candidates: list[FindingCandidate],
    now: datetime | None = None,
) -> bool:
    """Upsert open security findings and resolve cleared ones. Returns True if risk should refresh."""
    timestamp = now or datetime.now(UTC)
    active_codes = {candidate.code for candidate in candidates}
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
            category=candidate.category,
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
