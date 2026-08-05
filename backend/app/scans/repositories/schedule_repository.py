"""Asset scan schedule repository."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.scans.enums import SchedulePreset
from app.scans.schedule_models import AssetScanSchedule


def list_schedules_for_asset(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> list[AssetScanSchedule]:
    return (
        db.query(AssetScanSchedule)
        .filter(
            AssetScanSchedule.project_id == project_id,
            AssetScanSchedule.asset_id == asset_id,
        )
        .order_by(AssetScanSchedule.preset.asc())
        .all()
    )


def get_schedule_for_asset(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    preset: SchedulePreset,
) -> AssetScanSchedule | None:
    return (
        db.query(AssetScanSchedule)
        .filter(
            AssetScanSchedule.project_id == project_id,
            AssetScanSchedule.asset_id == asset_id,
            AssetScanSchedule.preset == preset,
        )
        .first()
    )


def create_schedule(db: Session, schedule: AssetScanSchedule) -> AssetScanSchedule:
    db.add(schedule)
    db.flush()
    return schedule


def list_due_schedules(db: Session, *, before: datetime) -> list[AssetScanSchedule]:
    return (
        db.query(AssetScanSchedule)
        .options(joinedload(AssetScanSchedule.asset))
        .filter(
            AssetScanSchedule.enabled.is_(True),
            AssetScanSchedule.next_run_at.isnot(None),
            AssetScanSchedule.next_run_at <= before,
        )
        .order_by(AssetScanSchedule.next_run_at.asc())
        .all()
    )
