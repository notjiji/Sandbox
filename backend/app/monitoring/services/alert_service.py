"""Persist operational monitoring alerts."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.service import record_audit_event
from app.monitoring.enums import AgentStatus, AlertStatus
from app.monitoring.events import MonitoringAuditAction
from app.monitoring.models import MonitoringAgent, MonitoringAlert
from app.monitoring.repositories.alert_repository import get_alert_by_code
from app.monitoring.services.alert_engine import (
    AlertCandidate,
    server_offline_alert,
    should_alert_offline,
)


def upsert_alerts(
    db: Session,
    *,
    agent: MonitoringAgent,
    candidates: list[AlertCandidate],
    now: datetime | None = None,
) -> None:
    timestamp = now or datetime.now(UTC)
    active_codes = {candidate.code for candidate in candidates}
    for candidate in candidates:
        _upsert_one(db, agent=agent, candidate=candidate, now=timestamp)

    open_alerts = (
        db.query(MonitoringAlert)
        .filter(
            MonitoringAlert.asset_id == agent.asset_id,
            MonitoringAlert.status == AlertStatus.OPEN,
        )
        .all()
    )
    for alert in open_alerts:
        if alert.alert_code not in active_codes:
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = timestamp
            db.add(alert)


def open_or_refresh_alert(
    db: Session,
    *,
    agent: MonitoringAgent,
    candidate: AlertCandidate,
    now: datetime | None = None,
) -> bool:
    """Open one alert without resolving others. Returns True if newly opened or reopened."""
    return _upsert_one(db, agent=agent, candidate=candidate, now=now or datetime.now(UTC))


def reconcile_offline_agent(db: Session, *, agent: MonitoringAgent, now: datetime | None = None) -> bool:
    timestamp = now or datetime.now(UTC)
    if not should_alert_offline(agent, now=timestamp):
        return False
    opened = open_or_refresh_alert(
        db, agent=agent, candidate=server_offline_alert(agent), now=timestamp
    )
    if agent.status == AgentStatus.ONLINE:
        agent.status = AgentStatus.OFFLINE
        db.add(agent)
    return opened


def reconcile_offline_agents(db: Session, agents: list[MonitoringAgent]) -> int:
    opened = 0
    now = datetime.now(UTC)
    for agent in agents:
        if reconcile_offline_agent(db, agent=agent, now=now):
            opened += 1
    if opened:
        db.flush()
    return opened


def _upsert_one(
    db: Session,
    *,
    agent: MonitoringAgent,
    candidate: AlertCandidate,
    now: datetime,
) -> bool:
    existing = get_alert_by_code(db, asset_id=agent.asset_id, alert_code=candidate.code)
    if existing is None:
        db.add(
            MonitoringAlert(
                organization_id=agent.organization_id,
                project_id=agent.project_id,
                asset_id=agent.asset_id,
                agent_id=agent.id,
                alert_code=candidate.code,
                title=candidate.title,
                message=candidate.message,
                evidence=candidate.evidence,
                severity=candidate.severity,
                status=AlertStatus.OPEN,
                first_seen_at=now,
                last_seen_at=now,
            )
        )
        record_audit_event(
            db,
            action=MonitoringAuditAction.ALERT_OPENED,
            user_id=None,
            organization_id=agent.organization_id,
            resource_type="monitoring_alert",
            resource_id=agent.asset_id,
            details={
                "asset_id": str(agent.asset_id),
                "project_id": str(agent.project_id),
                "alert_code": candidate.code,
                "severity": candidate.severity.value,
            },
        )
        return True

    existing.title = candidate.title
    existing.message = candidate.message
    existing.evidence = candidate.evidence
    existing.severity = candidate.severity
    existing.last_seen_at = now
    reopened = existing.status == AlertStatus.RESOLVED
    if reopened:
        existing.status = AlertStatus.OPEN
        existing.resolved_at = None
        existing.first_seen_at = now
    db.add(existing)
    return reopened
