import uuid
from datetime import UTC, datetime

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.scans.enums import ScanStatus, ScanType
from app.scans.lifecycle import transition_scan_status
from app.scans.models import Scan
from app.scans.schemas import ScanListQuery


def list_scans_for_asset(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> list[Scan]:
    return (
        db.query(Scan)
        .filter(Scan.project_id == project_id, Scan.asset_id == asset_id)
        .order_by(Scan.created_at.desc())
        .all()
    )


def list_scans_for_asset_paginated(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    query: ScanListQuery,
) -> tuple[list[Scan], int]:
    base = db.query(Scan).filter(Scan.project_id == project_id, Scan.asset_id == asset_id)

    if query.status is not None:
        base = base.filter(Scan.status == query.status)
    if query.scan_type is not None:
        base = base.filter(Scan.scan_type == query.scan_type)
    if query.search:
        needle = f"%{query.search.strip().lower()}%"
        base = base.filter(
            or_(
                cast(Scan.scan_type, String).ilike(needle),
                cast(Scan.status, String).ilike(needle),
            )
        )

    total = base.count()
    offset = (query.page - 1) * query.limit
    items = (
        base.order_by(Scan.created_at.desc())
        .offset(offset)
        .limit(query.limit)
        .all()
    )
    return items, int(total)


def get_scan_for_asset(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> Scan | None:
    return (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.project_id == project_id, Scan.asset_id == asset_id)
        .first()
    )


def list_scans_for_project(db: Session, *, project_id: uuid.UUID) -> list[Scan]:
    return (
        db.query(Scan)
        .filter(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .all()
    )


def get_scan_by_id_for_project(
    db: Session,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> Scan | None:
    return (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.project_id == project_id)
        .first()
    )


def create_scan(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_type: ScanType = ScanType.FULL,
    selected_plugins: list[str] | None = None,
    created_by: uuid.UUID | None = None,
) -> Scan:
    now = datetime.now(UTC)
    scan = Scan(
        project_id=project_id,
        asset_id=asset_id,
        scan_type=scan_type,
        selected_plugins=selected_plugins,
        status=ScanStatus.PENDING,
        pending_at=now,
        created_by=created_by,
    )
    db.add(scan)
    db.flush()
    return scan


def update_scan_status(db: Session, scan: Scan, *, status: ScanStatus) -> Scan:
    transition_scan_status(scan, status=status)
    db.add(scan)
    db.flush()
    return scan
