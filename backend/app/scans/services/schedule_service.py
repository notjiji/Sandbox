"""Per-asset scan schedule service."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.assets.enums import AssetStatus
from app.assets.services.asset_service import asset_service
from app.core.config import get_settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.members.models import OrganizationMember
from app.scans.enums import SchedulePreset, ScanStatus
from app.scans.lifecycle import transition_scan_status
from app.scans.profiles import SCAN_PROFILE_LABELS
from app.scans.repositories.scan_repository import create_scan
from app.scans.repositories.schedule_repository import (
    create_schedule,
    get_schedule_for_asset,
    list_due_schedules,
    list_schedules_for_asset,
)
from app.scans.schedule_models import AssetScanSchedule
from app.scans.schedule_presets import (
    SCHEDULE_PRESET_CONFIG,
    SCHEDULE_PRESET_ORDER,
    compute_next_run_at,
)
from app.scans.schemas import ScanScheduleListResponse, ScanScheduleSummary, UpdateScanScheduleRequest
from app.scans.services.scan_executor import run_queued_scan as _run_queued_scan

logger = get_logger("sandbox.scans.schedule")


def _profile_label(scan_type, selected_plugins: list | None) -> str:
    if scan_type.value == "custom" and selected_plugins:
        return ", ".join(selected_plugins)
    return SCAN_PROFILE_LABELS.get(scan_type, scan_type.value)


def to_schedule_summary(schedule: AssetScanSchedule) -> ScanScheduleSummary:
    config = SCHEDULE_PRESET_CONFIG[schedule.preset]
    return ScanScheduleSummary(
        id=str(schedule.id),
        preset=schedule.preset,
        label=config.label,
        cadence=config.cadence,
        scan_type=schedule.scan_type,
        profile_label=_profile_label(schedule.scan_type, schedule.selected_plugins),
        enabled=schedule.enabled,
        last_run_at=schedule.last_run_at,
        next_run_at=schedule.next_run_at,
        last_scan_id=str(schedule.last_scan_id) if schedule.last_scan_id else None,
    )


def _ensure_default_schedules(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> list[AssetScanSchedule]:
    existing = list_schedules_for_asset(db, project_id=project_id, asset_id=asset_id)
    by_preset = {schedule.preset: schedule for schedule in existing}

    for preset in SCHEDULE_PRESET_ORDER:
        if preset in by_preset:
            continue
        config = SCHEDULE_PRESET_CONFIG[preset]
        schedule = AssetScanSchedule(
            project_id=project_id,
            asset_id=asset_id,
            preset=preset,
            scan_type=config.scan_type,
            selected_plugins=config.selected_plugins,
            enabled=False,
            next_run_at=compute_next_run_at(preset),
        )
        create_schedule(db, schedule)
        by_preset[preset] = schedule

    db.flush()
    return [by_preset[preset] for preset in SCHEDULE_PRESET_ORDER]


def list_asset_scan_schedules(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> ScanScheduleListResponse:
    asset_service.get_for_project(db, membership, project_id=project_id, asset_id=asset_id)
    schedules = _ensure_default_schedules(db, project_id=project_id, asset_id=asset_id)
    db.commit()
    return ScanScheduleListResponse(items=[to_schedule_summary(schedule) for schedule in schedules])


def update_asset_scan_schedule(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    preset: SchedulePreset,
    body: UpdateScanScheduleRequest,
) -> ScanScheduleSummary:
    asset_service.get_for_project(db, membership, project_id=project_id, asset_id=asset_id)
    _ensure_default_schedules(db, project_id=project_id, asset_id=asset_id)
    schedule = get_schedule_for_asset(
        db, project_id=project_id, asset_id=asset_id, preset=preset
    )
    if not schedule:
        raise NotFoundError("Scan schedule")

    schedule.enabled = body.enabled
    if body.enabled:
        schedule.next_run_at = compute_next_run_at(
            preset,
            last_run_at=schedule.last_run_at,
        )
    db.add(schedule)
    db.commit()
    db.refresh(schedule)
    return to_schedule_summary(schedule)


def _execute_scheduled_scan(db: Session, schedule: AssetScanSchedule) -> uuid.UUID:
    scan = create_scan(
        db,
        project_id=schedule.project_id,
        asset_id=schedule.asset_id,
        scan_type=schedule.scan_type,
        selected_plugins=schedule.selected_plugins,
        created_by=None,
    )
    transition_scan_status(scan, status=ScanStatus.QUEUED)
    db.flush()

    settings = get_settings()
    if settings.SCAN_RUN_INLINE:
        _run_queued_scan(
            db,
            scan_id=scan.id,
            project_id=schedule.project_id,
            asset_id=schedule.asset_id,
        )
    else:
        from app.jobs.scans import execute_scan

        execute_scan.delay(
            scan_id=str(scan.id),
            project_id=str(schedule.project_id),
            asset_id=str(schedule.asset_id),
        )
    return scan.id


def fire_due_schedules(db: Session) -> int:
    now = datetime.now(UTC)
    due = list_due_schedules(db, before=now)
    fired = 0

    for schedule in due:
        try:
            asset = schedule.asset
            if asset is None or asset.status != AssetStatus.ACTIVE or asset.deleted_at is not None:
                schedule.enabled = False
                db.add(schedule)
                continue

            scan_id = _execute_scheduled_scan(db, schedule)
            schedule.last_run_at = now
            schedule.last_scan_id = scan_id
            schedule.next_run_at = compute_next_run_at(
                schedule.preset,
                reference=now,
                last_run_at=now,
            )
            db.add(schedule)
            fired += 1
        except Exception:
            logger.exception(
                "scheduled scan failed",
                extra={
                    "schedule_id": str(schedule.id),
                    "asset_id": str(schedule.asset_id),
                    "preset": schedule.preset.value,
                },
            )

    if fired or due:
        db.commit()
    return fired
