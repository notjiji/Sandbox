import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.monitoring.enums import MAX_SNAPSHOTS
from app.monitoring.metric_types import DISK_USAGE, HISTORY_METRIC_TYPES, ROOT_FILESYSTEMS
from app.monitoring.models import MonitoringMetric
from app.monitoring.services.metric_normalizer import MetricPoint


def insert_metrics(
    db: Session,
    *,
    agent_id: uuid.UUID,
    asset_id: uuid.UUID,
    collected_at: datetime,
    points: list[MetricPoint],
) -> None:
    for point in points:
        db.add(
            MonitoringMetric(
                agent_id=agent_id,
                asset_id=asset_id,
                metric_type=point.metric_type,
                value=point.value,
                unit=point.unit,
                collected_at=collected_at,
                labels=point.labels,
            )
        )
    if points:
        db.flush()


def prune_metrics(db: Session, *, asset_id: uuid.UUID, keep: int = MAX_SNAPSHOTS) -> None:
    cutoff = (
        db.query(MonitoringMetric.collected_at)
        .filter(MonitoringMetric.asset_id == asset_id)
        .distinct()
        .order_by(MonitoringMetric.collected_at.desc())
        .offset(keep)
        .limit(1)
        .scalar()
    )
    if cutoff is None:
        return
    db.query(MonitoringMetric).filter(
        MonitoringMetric.asset_id == asset_id,
        MonitoringMetric.collected_at <= cutoff,
    ).delete(synchronize_session=False)


def list_metrics_since(
    db: Session,
    *,
    asset_id: uuid.UUID,
    since: datetime,
    metric_types: tuple[str, ...] = HISTORY_METRIC_TYPES,
    limit: int = 30000,
) -> list[MonitoringMetric]:
    return (
        db.query(MonitoringMetric)
        .filter(
            MonitoringMetric.asset_id == asset_id,
            MonitoringMetric.metric_type.in_(metric_types),
            MonitoringMetric.collected_at >= since,
        )
        .order_by(MonitoringMetric.collected_at.asc())
        .limit(limit)
        .all()
    )


def get_latest_metrics_for_assets(
    db: Session,
    *,
    asset_ids: list[uuid.UUID],
    metric_types: tuple[str, ...] = HISTORY_METRIC_TYPES,
) -> dict[uuid.UUID, dict[str, MonitoringMetric]]:
    if not asset_ids:
        return {}
    latest_ts = (
        db.query(
            MonitoringMetric.asset_id,
            MonitoringMetric.metric_type,
            func.max(MonitoringMetric.collected_at).label("max_ts"),
        )
        .filter(
            MonitoringMetric.asset_id.in_(asset_ids),
            MonitoringMetric.metric_type.in_(metric_types),
        )
        .group_by(MonitoringMetric.asset_id, MonitoringMetric.metric_type)
        .subquery()
    )
    rows = (
        db.query(MonitoringMetric)
        .join(
            latest_ts,
            (MonitoringMetric.asset_id == latest_ts.c.asset_id)
            & (MonitoringMetric.metric_type == latest_ts.c.metric_type)
            & (MonitoringMetric.collected_at == latest_ts.c.max_ts),
        )
        .all()
    )
    result: dict[uuid.UUID, dict[str, MonitoringMetric]] = {}
    for row in rows:
        fold_metric(result.setdefault(row.asset_id, {}), row)
    return result


def fold_metric(bucket: dict[str, MonitoringMetric], row: MonitoringMetric) -> None:
    existing = bucket.get(row.metric_type)
    if existing is None or _is_preferred_disk(row, existing):
        bucket[row.metric_type] = row


def _is_preferred_disk(candidate: MonitoringMetric, current: MonitoringMetric) -> bool:
    if candidate.metric_type != DISK_USAGE:
        return False
    candidate_fs = (candidate.labels or {}).get("filesystem")
    current_fs = (current.labels or {}).get("filesystem")
    return candidate_fs in ROOT_FILESYSTEMS and current_fs not in ROOT_FILESYSTEMS
