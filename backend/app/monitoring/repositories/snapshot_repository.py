import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.monitoring.enums import MAX_SNAPSHOTS
from app.monitoring.models import MonitoringSnapshot


def create_snapshot(
    db: Session,
    *,
    agent_id: uuid.UUID,
    asset_id: uuid.UUID,
    collected_at: datetime,
    payload: dict | None,
) -> MonitoringSnapshot:
    snapshot = MonitoringSnapshot(
        agent_id=agent_id,
        asset_id=asset_id,
        collected_at=collected_at,
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


def get_latest_snapshots_for_assets(
    db: Session,
    *,
    asset_ids: list[uuid.UUID],
) -> dict[uuid.UUID, MonitoringSnapshot]:
    if not asset_ids:
        return {}
    latest_ts = (
        db.query(
            MonitoringSnapshot.asset_id,
            func.max(MonitoringSnapshot.collected_at).label("max_ts"),
        )
        .filter(MonitoringSnapshot.asset_id.in_(asset_ids))
        .group_by(MonitoringSnapshot.asset_id)
        .subquery()
    )
    rows = (
        db.query(MonitoringSnapshot)
        .join(
            latest_ts,
            (MonitoringSnapshot.asset_id == latest_ts.c.asset_id)
            & (MonitoringSnapshot.collected_at == latest_ts.c.max_ts),
        )
        .all()
    )
    return {row.asset_id: row for row in rows}
