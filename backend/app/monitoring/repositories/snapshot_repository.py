import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.monitoring.enums import MAX_SNAPSHOTS
from app.monitoring.models import MonitoringSnapshot


def create_snapshot(
    db: Session,
    *,
    agent_id: uuid.UUID,
    asset_id: uuid.UUID,
    collected_at: datetime,
    cpu_percent: float | None,
    ram_percent: float | None,
    ram_used_mb: float | None,
    ram_total_mb: float | None,
    disk_percent: float | None,
    disk_used_gb: float | None,
    disk_total_gb: float | None,
    uptime_seconds: int | None,
    load_avg_1: float | None,
    process_count: int | None,
    payload: dict | None,
) -> MonitoringSnapshot:
    snapshot = MonitoringSnapshot(
        agent_id=agent_id,
        asset_id=asset_id,
        collected_at=collected_at,
        cpu_percent=cpu_percent,
        ram_percent=ram_percent,
        ram_used_mb=ram_used_mb,
        ram_total_mb=ram_total_mb,
        disk_percent=disk_percent,
        disk_used_gb=disk_used_gb,
        disk_total_gb=disk_total_gb,
        uptime_seconds=uptime_seconds,
        load_avg_1=load_avg_1,
        process_count=process_count,
        payload=payload,
    )
    db.add(snapshot)
    db.flush()
    return snapshot


def prune_snapshots(db: Session, *, asset_id: uuid.UUID, keep: int = MAX_SNAPSHOTS) -> None:
    extra_ids = [
        row[0]
        for row in (
            db.query(MonitoringSnapshot.id)
            .filter(MonitoringSnapshot.asset_id == asset_id)
            .order_by(MonitoringSnapshot.collected_at.desc())
            .offset(keep)
            .all()
        )
    ]
    if extra_ids:
        db.query(MonitoringSnapshot).filter(MonitoringSnapshot.id.in_(extra_ids)).delete(
            synchronize_session=False
        )


def get_latest_snapshot(db: Session, *, asset_id: uuid.UUID) -> MonitoringSnapshot | None:
    return (
        db.query(MonitoringSnapshot)
        .filter(MonitoringSnapshot.asset_id == asset_id)
        .order_by(MonitoringSnapshot.collected_at.desc())
        .first()
    )


def list_snapshots_since(
    db: Session,
    *,
    asset_id: uuid.UUID,
    since: datetime,
    limit: int = MAX_SNAPSHOTS,
) -> list[MonitoringSnapshot]:
    return (
        db.query(MonitoringSnapshot)
        .filter(
            MonitoringSnapshot.asset_id == asset_id,
            MonitoringSnapshot.collected_at >= since,
        )
        .order_by(MonitoringSnapshot.collected_at.asc())
        .limit(limit)
        .all()
    )


def get_latest_snapshots_for_assets(
    db: Session,
    *,
    asset_ids: list[uuid.UUID],
) -> dict[uuid.UUID, MonitoringSnapshot]:
    if not asset_ids:
        return {}
    snapshots = (
        db.query(MonitoringSnapshot)
        .filter(MonitoringSnapshot.asset_id.in_(asset_ids))
        .order_by(MonitoringSnapshot.collected_at.desc())
        .all()
    )
    latest: dict[uuid.UUID, MonitoringSnapshot] = {}
    for snapshot in snapshots:
        if snapshot.asset_id not in latest:
            latest[snapshot.asset_id] = snapshot
    return latest
