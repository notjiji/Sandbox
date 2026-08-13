import uuid
from collections import defaultdict
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.assets.repositories.asset_repository import get_asset_by_id
from app.members.models import OrganizationMember
from app.monitoring.enums import DEFAULT_HISTORY_HOURS, MAX_HISTORY_HOURS, AgentStatus
from app.monitoring.metric_types import (
    CPU_USAGE,
    DISK_USAGE,
    HISTORY_METRIC_TYPES,
    MEMORY_USAGE,
    PROCESS_COUNT,
    UPTIME,
)
from app.monitoring.models import MonitoringAgent, MonitoringAlert, MonitoringMetric
from app.monitoring.repositories.agent_repository import (
    effective_status,
    get_agent_by_asset,
    list_agents_for_organization,
)
from app.monitoring.repositories.alert_repository import (
    count_open_alerts_for_assets,
    count_open_alerts_for_organization,
    list_alerts_for_asset,
)
from app.monitoring.repositories.metric_repository import (
    fold_metric,
    get_latest_metrics_for_assets,
    list_metrics_since,
)
from app.monitoring.repositories.snapshot_repository import get_latest_snapshot
from app.monitoring.schemas import (
    AgentSummary,
    AlertSummary,
    MetricsPayload,
    MonitoringOverview,
    OrgMonitoringOverview,
    OrgMonitoringServer,
    SecurityPayload,
    SnapshotSummary,
)
from app.projects.validators import require_org_asset

_LATEST_METRIC_TYPES = HISTORY_METRIC_TYPES + (UPTIME, PROCESS_COUNT)


def _agent_summary(agent: MonitoringAgent, *, asset_name: str | None = None) -> AgentSummary:
    return AgentSummary(
        id=str(agent.id),
        asset_id=str(agent.asset_id),
        asset_name=asset_name,
        project_id=str(agent.project_id),
        status=effective_status(agent),
        hostname=agent.hostname,
        agent_version=agent.agent_version,
        last_seen_at=agent.last_seen_at,
        enrolled_at=agent.enrolled_at,
    )


def _metric_value(by_type: dict[str, MonitoringMetric], metric_type: str) -> float | None:
    row = by_type.get(metric_type)
    return row.value if row is not None else None


def _metric_int(by_type: dict[str, MonitoringMetric], metric_type: str) -> int | None:
    value = _metric_value(by_type, metric_type)
    return int(value) if value is not None else None


def _snapshot_summary(
    collected_at: datetime,
    by_type: dict[str, MonitoringMetric],
) -> SnapshotSummary:
    return SnapshotSummary(
        collected_at=collected_at,
        cpu_percent=_metric_value(by_type, CPU_USAGE),
        ram_percent=_metric_value(by_type, MEMORY_USAGE),
        disk_percent=_metric_value(by_type, DISK_USAGE),
        uptime_seconds=_metric_int(by_type, UPTIME),
        process_count=_metric_int(by_type, PROCESS_COUNT),
    )


def _history_summaries(rows: list[MonitoringMetric]) -> list[SnapshotSummary]:
    grouped: dict[datetime, dict[str, MonitoringMetric]] = defaultdict(dict)
    for row in rows:
        fold_metric(grouped[row.collected_at], row)
    return [_snapshot_summary(ts, by_type) for ts, by_type in sorted(grouped.items())]


def _alert_summary(alert: MonitoringAlert) -> AlertSummary:
    return AlertSummary(
        id=str(alert.id),
        alert_code=alert.alert_code,
        title=alert.title,
        message=alert.message,
        evidence=alert.evidence,
        severity=alert.severity,
        status=alert.status,
        first_seen_at=alert.first_seen_at,
        last_seen_at=alert.last_seen_at,
        resolved_at=alert.resolved_at,
    )


def get_asset_monitoring(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    hours: int = DEFAULT_HISTORY_HOURS,
) -> MonitoringOverview:
    asset = require_org_asset(db, membership, project_id=project_id, asset_id=asset_id)
    agent = get_agent_by_asset(db, asset_id=asset.id)
    if agent is None:
        return MonitoringOverview()

    window = min(max(hours, 1), MAX_HISTORY_HOURS)
    since = datetime.now(UTC) - timedelta(hours=window)
    latest = get_latest_snapshot(db, asset_id=asset.id)
    latest_metrics = get_latest_metrics_for_assets(
        db, asset_ids=[asset.id], metric_types=_LATEST_METRIC_TYPES
    ).get(asset.id, {})
    history_rows = list_metrics_since(db, asset_id=asset.id, since=since)
    alerts = list_alerts_for_asset(db, asset_id=asset.id)

    metrics = None
    security = None
    if latest and latest.payload:
        raw_metrics = latest.payload.get("metrics") or {}
        raw_security = latest.payload.get("security") or {}
        try:
            metrics = MetricsPayload.model_validate(raw_metrics)
        except Exception:
            metrics = None
        try:
            security = SecurityPayload.model_validate(raw_security)
        except Exception:
            security = None

    collected_at = latest.collected_at if latest else None
    latest_summary = (
        _snapshot_summary(collected_at, latest_metrics) if collected_at is not None else None
    )

    return MonitoringOverview(
        agent=_agent_summary(agent, asset_name=asset.name),
        latest=latest_summary,
        metrics=metrics,
        security=security,
        alerts=[_alert_summary(alert) for alert in alerts],
        history=_history_summaries(history_rows),
    )


def get_organization_monitoring(
    db: Session,
    membership: OrganizationMember,
) -> OrgMonitoringOverview:
    agents = list_agents_for_organization(db, organization_id=membership.organization_id)
    asset_ids = [agent.asset_id for agent in agents]
    latest_by_asset = get_latest_metrics_for_assets(db, asset_ids=asset_ids)
    open_by_asset = count_open_alerts_for_assets(db, asset_ids=asset_ids)

    servers: list[OrgMonitoringServer] = []
    online = offline = pending = 0
    for agent in agents:
        status = effective_status(agent)
        if status == AgentStatus.ONLINE:
            online += 1
        elif status == AgentStatus.PENDING:
            pending += 1
        else:
            offline += 1
        asset = get_asset_by_id(db, project_id=agent.project_id, asset_id=agent.asset_id)
        by_type = latest_by_asset.get(agent.asset_id, {})
        servers.append(
            OrgMonitoringServer(
                asset_id=str(agent.asset_id),
                asset_name=asset.name if asset else "Unknown",
                project_id=str(agent.project_id),
                status=status,
                hostname=agent.hostname,
                cpu_percent=_metric_value(by_type, CPU_USAGE),
                ram_percent=_metric_value(by_type, MEMORY_USAGE),
                disk_percent=_metric_value(by_type, DISK_USAGE),
                open_alerts=open_by_asset.get(agent.asset_id, 0),
                last_seen_at=agent.last_seen_at,
            )
        )

    return OrgMonitoringOverview(
        agents_online=online,
        agents_offline=offline,
        agents_pending=pending,
        open_alerts=count_open_alerts_for_organization(
            db, organization_id=membership.organization_id
        ),
        servers=servers,
    )
