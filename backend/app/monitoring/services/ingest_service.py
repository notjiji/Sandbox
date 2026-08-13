from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.service import record_audit_event
from app.monitoring.enums import AgentStatus, AlertStatus
from app.monitoring.events import MonitoringAuditAction
from app.monitoring.models import MonitoringAgent, MonitoringAlert
from app.monitoring.repositories.alert_repository import (
    count_open_alerts_for_assets,
    get_alert_by_code,
)
from app.monitoring.repositories.metric_repository import insert_metrics, prune_metrics
from app.monitoring.repositories.snapshot_repository import create_snapshot, prune_snapshots
from app.monitoring.schemas import AgentIngestRequest, AgentIngestResponse
from app.monitoring.services.alert_engine import evaluate_ingest
from app.monitoring.services.metric_normalizer import normalize_metrics


def ingest_agent_payload(
    db: Session,
    *,
    agent: MonitoringAgent,
    body: AgentIngestRequest,
) -> AgentIngestResponse:
    now = datetime.now(UTC)
    collected_at = body.collected_at or now
    if collected_at.tzinfo is None:
        collected_at = collected_at.replace(tzinfo=UTC)

    metrics = body.metrics
    payload = {
        "metrics": metrics.model_dump(mode="json"),
        "security": body.security.model_dump(mode="json"),
        "hostname": body.hostname,
        "agent_version": body.agent_version,
    }

    create_snapshot(
        db,
        agent_id=agent.id,
        asset_id=agent.asset_id,
        collected_at=collected_at,
        payload=payload,
    )
    insert_metrics(
        db,
        agent_id=agent.id,
        asset_id=agent.asset_id,
        collected_at=collected_at,
        points=normalize_metrics(metrics),
    )
    prune_snapshots(db, asset_id=agent.asset_id)
    prune_metrics(db, asset_id=agent.asset_id)

    agent.status = AgentStatus.ONLINE
    agent.last_seen_at = now
    if body.hostname:
        agent.hostname = body.hostname
    if body.agent_version:
        agent.agent_version = body.agent_version
    db.add(agent)

    candidates = evaluate_ingest(body)
    active_codes = {candidate.code for candidate in candidates}
    for candidate in candidates:
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
        else:
            existing.title = candidate.title
            existing.message = candidate.message
            existing.evidence = candidate.evidence
            existing.severity = candidate.severity
            existing.last_seen_at = now
            if existing.status == AlertStatus.RESOLVED:
                existing.status = AlertStatus.OPEN
                existing.resolved_at = None
                existing.first_seen_at = now
            db.add(existing)

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
            alert.resolved_at = now
            db.add(alert)

    from app.findings.services.monitoring_finding_sync import sync_monitoring_findings
    from app.core.risk_engine.engine import risk_engine

    risk_dirty = sync_monitoring_findings(
        db,
        project_id=agent.project_id,
        asset_id=agent.asset_id,
        candidates=candidates,
        active_codes=active_codes,
        now=now,
    )
    if risk_dirty:
        risk_engine.calculate_asset_risk(db, asset_id=agent.asset_id, store=True)
        risk_engine.calculate_project_risk(db, project_id=agent.project_id, store=True)
        risk_engine.calculate_organization_risk(db, organization_id=agent.organization_id, store=True)

    db.flush()
    remaining = count_open_alerts_for_assets(db, asset_ids=[agent.asset_id]).get(agent.asset_id, 0)
    return AgentIngestResponse(
        accepted=True,
        agent_status=AgentStatus.ONLINE,
        alerts_open=remaining,
    )
