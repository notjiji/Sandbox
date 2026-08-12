import uuid
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.monitoring.enums import AlertStatus
from app.monitoring.models import MonitoringAlert


def get_alert_by_code(
    db: Session,
    *,
    asset_id: uuid.UUID,
    alert_code: str,
) -> MonitoringAlert | None:
    return (
        db.query(MonitoringAlert)
        .filter(MonitoringAlert.asset_id == asset_id, MonitoringAlert.alert_code == alert_code)
        .first()
    )


def list_alerts_for_asset(
    db: Session,
    *,
    asset_id: uuid.UUID,
    status: AlertStatus | None = None,
) -> list[MonitoringAlert]:
    query = db.query(MonitoringAlert).filter(MonitoringAlert.asset_id == asset_id)
    if status is not None:
        query = query.filter(MonitoringAlert.status == status)
    return query.order_by(MonitoringAlert.last_seen_at.desc()).all()


def count_open_alerts_for_assets(
    db: Session,
    *,
    asset_ids: list[uuid.UUID],
) -> dict[uuid.UUID, int]:
    if not asset_ids:
        return {}
    rows = (
        db.query(MonitoringAlert.asset_id, func.count(MonitoringAlert.id))
        .filter(
            MonitoringAlert.asset_id.in_(asset_ids),
            MonitoringAlert.status == AlertStatus.OPEN,
        )
        .group_by(MonitoringAlert.asset_id)
        .all()
    )
    return {asset_id: int(count) for asset_id, count in rows}


def count_open_alerts_for_organization(db: Session, *, organization_id: uuid.UUID) -> int:
    return int(
        db.query(func.count(MonitoringAlert.id))
        .filter(
            MonitoringAlert.organization_id == organization_id,
            MonitoringAlert.status == AlertStatus.OPEN,
        )
        .scalar()
        or 0
    )
