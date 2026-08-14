"""Executes queued scans — shared by API inline mode and Celery workers."""

import uuid

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.risk_engine.engine import risk_engine
from app.core.scan_engine.orchestrator import scan_orchestrator
from app.projects.models import Project
from app.scans.audit import record_scan_audit
from app.scans.enums import ScanStatus
from app.scans.events import ScanAuditAction
from app.scans.lifecycle import transition_scan_status
from app.scans.repositories.scan_plugin_repository import list_plugin_runs_for_scan
from app.scans.repositories.scan_repository import get_scan_for_asset, update_scan_status

logger = get_logger("sandbox.scan_executor")


def run_queued_scan(
    db: Session,
    *,
    scan_id: uuid.UUID,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> None:
    """Transition queued → running → completed/failed."""
    scan = get_scan_for_asset(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=scan_id,
    )
    if not scan:
        logger.warning("scan not found for execution", extra={"scan_id": str(scan_id)})
        return

    if scan.status != ScanStatus.QUEUED:
        logger.info(
            "skipping scan execution — not queued",
            extra={"scan_id": str(scan_id), "status": scan.status.value},
        )
        return

    transition_scan_status(scan, status=ScanStatus.RUNNING)
    db.add(scan)
    db.flush()
    record_scan_audit(db, scan, action=ScanAuditAction.STARTED)

    try:
        scan_orchestrator.execute(db, scan=scan, project_id=project_id, asset_id=asset_id)
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            risk_engine.recalculate_after_scan(
                db,
                project_id=project_id,
                asset_id=asset_id,
                scan_id=scan_id,
                organization_id=project.organization_id,
            )
    except Exception:
        logger.exception("scan orchestration raised", extra={"scan_id": str(scan_id)})
        db.refresh(scan)
        if scan.status == ScanStatus.RUNNING:
            update_scan_status(db, scan, status=ScanStatus.FAILED)

    if scan.status == ScanStatus.COMPLETED:
        record_scan_audit(db, scan, action=ScanAuditAction.COMPLETED)
    elif scan.status == ScanStatus.FAILED:
        record_scan_audit(db, scan, action=ScanAuditAction.FAILED)

    scan.plugin_runs = list_plugin_runs_for_scan(db, scan_id=scan.id)
