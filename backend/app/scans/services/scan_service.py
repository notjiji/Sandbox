import uuid

from sqlalchemy.orm import Session

from app.assets.service import asset_service
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.scan_engine.orchestrator import scan_orchestrator
from app.members.models import OrganizationMember
from app.scans.enums import ScanStatus
from app.scans.events import ScanAuditAction
from app.scans.models import Scan
from app.scans.repositories.scan_repository import (
    create_scan,
    get_scan_for_asset,
    list_scans_for_asset,
    update_scan_status,
)
from app.scans.schemas import CreateAssetScanRequest, ScanListResponse, ScanSummary
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


def _require_asset(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    asset_service.get_for_project(db, membership, project_id=project_id, asset_id=asset_id)


def list_asset_scans(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> ScanListResponse:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    scans = list_scans_for_asset(db, project_id=project_id, asset_id=asset_id)
    items = [to_scan_summary(scan) for scan in scans]
    return ScanListResponse(items=items, total=len(items))


def create_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: CreateAssetScanRequest,
) -> ScanSummary:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
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


def get_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    scan = get_scan_for_asset(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)
    if not scan:
        raise NotFoundError("Scan")
    return to_scan_summary(scan)


def run_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    asset_service.get_for_project(db, membership, project_id=project_id, asset_id=asset_id)
    scan = get_scan_for_asset(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)
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
    db.flush()

    scan_orchestrator.execute(db, scan=scan, project_id=project_id, asset_id=asset_id)
    db.commit()
    db.refresh(scan)
    return to_scan_summary(scan)


def cancel_asset_scan(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> ScanSummary:
    _require_asset(db, membership, project_id=project_id, asset_id=asset_id)
    scan = get_scan_for_asset(db, project_id=project_id, asset_id=asset_id, scan_id=scan_id)
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
