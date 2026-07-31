import uuid

from sqlalchemy.orm import Session

from app.assets.repository import get_asset_by_id
from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.scans.events import ScanAuditAction
from app.scans.models import Scan
from app.scans.enums import ScanStatus
from app.scans.repository import create_scan, get_scan_by_id, list_scans_for_project, update_scan_status
from app.scans.schemas import CreateScanRequest, ScanListResponse, ScanSummary
from app.audit.service import record_audit_event


def to_scan_summary(scan: Scan) -> ScanSummary:
    return ScanSummary(
        id=str(scan.id),
        project_id=str(scan.project_id),
        asset_id=str(scan.asset_id),
        status=scan.status,
        scan_type=scan.scan_type,
        created_by=str(scan.created_by) if scan.created_by else None,
        started_at=scan.started_at,
        completed_at=scan.completed_at,
    )


def list_project_scans(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> ScanListResponse:
    require_active_project(db, membership, project_id)
    scans = list_scans_for_project(db, project_id=project_id)
    items = [to_scan_summary(scan) for scan in scans]
    return ScanListResponse(items=items, total=len(items))


def create_project_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: CreateScanRequest,
) -> ScanSummary:
    require_active_project(db, membership, project_id)
    try:
        asset_id = uuid.UUID(body.asset_id)
    except ValueError as exc:
        raise ValidationAppError("Invalid asset_id") from exc

    asset = get_asset_by_id(db, project_id=project_id, asset_id=asset_id)
    if not asset:
        raise NotFoundError("Asset")

    scan = create_scan(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_type=body.scan_type,
        created_by=membership.user_id,
    )
    record_audit_event(
        db,
        action=ScanAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="scan",
        resource_id=scan.id,
        details={"project_id": str(project_id), "asset_id": str(asset_id)},
    )
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)


def get_project_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    require_active_project(db, membership, project_id)
    scan = get_scan_by_id(db, project_id=project_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    return to_scan_summary(scan)


def run_project_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    require_active_project(db, membership, project_id)
    scan = get_scan_by_id(db, project_id=project_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    if scan.status not in {ScanStatus.PENDING, ScanStatus.FAILED}:
        raise ValidationAppError("Scan cannot be started in its current state")

    update_scan_status(db, scan, status=ScanStatus.RUNNING)
    record_audit_event(
        db,
        action=ScanAuditAction.RUN,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="scan",
        resource_id=scan.id,
    )
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)


def cancel_project_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    require_active_project(db, membership, project_id)
    scan = get_scan_by_id(db, project_id=project_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    if scan.status not in {ScanStatus.PENDING, ScanStatus.RUNNING}:
        raise ValidationAppError("Scan cannot be cancelled in its current state")

    update_scan_status(db, scan, status=ScanStatus.CANCELLED)
    record_audit_event(
        db,
        action=ScanAuditAction.CANCEL,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="scan",
        resource_id=scan.id,
    )
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)
