import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.models.scan import Scan, ScanStatus, ScanType


def list_scans_for_project(db: Session, *, project_id: uuid.UUID) -> list[Scan]:
    return (
        db.query(Scan)
        .filter(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .all()
    )


def get_scan_by_id(
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
    created_by: uuid.UUID | None = None,
) -> Scan:
    scan = Scan(
        project_id=project_id,
        asset_id=asset_id,
        scan_type=scan_type,
        status=ScanStatus.PENDING,
        created_by=created_by,
    )
    db.add(scan)
    db.flush()
    return scan


def update_scan_status(db: Session, scan: Scan, *, status: ScanStatus) -> Scan:
    scan.status = status
    if status == ScanStatus.RUNNING and scan.started_at is None:
        scan.started_at = datetime.now(UTC)
    if status in {ScanStatus.COMPLETED, ScanStatus.FAILED, ScanStatus.CANCELLED}:
        scan.completed_at = datetime.now(UTC)
    db.add(scan)
    db.flush()
    return scan
