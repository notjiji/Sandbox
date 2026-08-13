from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.risk_engine.engine import risk_engine
from app.findings.services.monitoring_finding_sync import sync_monitoring_findings
from app.monitoring.enums import AGENT_HEARTBEAT_SECONDS, AgentStatus
from app.monitoring.models import MonitoringAgent
from app.monitoring.repositories.alert_repository import count_open_alerts_for_assets
from app.monitoring.repositories.metric_repository import insert_metrics, prune_metrics
from app.monitoring.repositories.snapshot_repository import create_snapshot, prune_snapshots
from app.monitoring.schemas import AgentIngestRequest, AgentIngestResponse
from app.monitoring.services.alert_engine import evaluate_alerts
from app.monitoring.services.alert_service import upsert_alerts
from app.monitoring.services.finding_engine import evaluate_findings
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

    alerts = evaluate_alerts(body)
    upsert_alerts(db, agent=agent, candidates=alerts, now=now)

    findings = evaluate_findings(body)
    risk_dirty = sync_monitoring_findings(
        db,
        project_id=agent.project_id,
        asset_id=agent.asset_id,
        candidates=findings,
        now=now,
    )
    if risk_dirty:
        risk_engine.recalculate_after_monitoring(
            db,
            project_id=agent.project_id,
            asset_id=agent.asset_id,
            organization_id=agent.organization_id,
        )

    db.flush()
    remaining = count_open_alerts_for_assets(db, asset_ids=[agent.asset_id]).get(agent.asset_id, 0)
    return AgentIngestResponse(
        accepted=True,
        agent_status=AgentStatus.ONLINE,
        alerts_open=remaining,
        next_interval_seconds=AGENT_HEARTBEAT_SECONDS,
    )
