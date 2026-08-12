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
from app.monitoring.repositories.snapshot_repository import create_snapshot, prune_snapshots
from app.monitoring.schemas import AgentIngestRequest, AgentIngestResponse
from app.monitoring.services.alert_engine import evaluate_ingest


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
    cpu_percent = metrics.cpu_usage if metrics.cpu_usage is not None else metrics.cpu_percent
    ram_percent = metrics.usage_percent if metrics.usage_percent is not None else metrics.ram_percent
    ram_used_mb = metrics.used_mb if metrics.used_mb is not None else metrics.ram_used_mb
    ram_total_mb = metrics.total_mb if metrics.total_mb is not None else metrics.ram_total_mb
    load_avg_1 = metrics.load_1m
    if load_avg_1 is None and metrics.load_avg:
        load_avg_1 = metrics.load_avg[0]
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
        cpu_percent=cpu_percent,
        ram_percent=ram_percent,
        ram_used_mb=ram_used_mb,
        ram_total_mb=ram_total_mb,
        disk_percent=metrics.disk_percent,
        disk_used_gb=metrics.disk_used_gb,
        disk_total_gb=metrics.disk_total_gb,
        uptime_seconds=metrics.uptime_seconds,
        load_avg_1=load_avg_1,
        process_count=metrics.process_count,
        payload=payload,
    )
    prune_snapshots(db, asset_id=agent.asset_id)

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

    db.flush()
    remaining = count_open_alerts_for_assets(db, asset_ids=[agent.asset_id]).get(agent.asset_id, 0)
    return AgentIngestResponse(
        accepted=True,
        agent_status=AgentStatus.ONLINE,
        alerts_open=remaining,
    )
