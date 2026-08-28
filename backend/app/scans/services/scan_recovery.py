"""Mark scans/reports stuck after worker loss or task timeout."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.reports.enums import ReportStatus
from app.reports.models import Report
from app.reports.repositories.report_repository import update_report
from app.scans.audit import record_scan_audit
from app.scans.enums import ScanStatus
from app.scans.events import ScanAuditAction
from app.scans.models import Scan
from app.scans.repositories.scan_repository import update_scan_status

logger = get_logger("sandbox.job_recovery")


def fail_running_scan(
    db: Session,
    *,
    scan_id: uuid.UUID,
    reason: str,
) -> bool:
    scan = db.query(Scan).filter(Scan.id == scan_id).first()
    if scan is None or scan.status != ScanStatus.RUNNING:
        return False

    update_scan_status(db, scan, status=ScanStatus.FAILED)
    record_scan_audit(
        db,
        scan,
        action=ScanAuditAction.FAILED,
        extra={"reason": reason},
    )
    logger.error(
        "scan marked failed after worker error",
        extra={"scan_id": str(scan_id), "reason": reason},
    )
    return True


def fail_generating_report(
    db: Session,
    *,
    report_id: uuid.UUID,
    reason: str,
) -> bool:
    report = db.query(Report).filter(Report.id == report_id).first()
    if report is None or report.status != ReportStatus.GENERATING:
        return False

    update_report(db, report, status=ReportStatus.FAILED)
    logger.error(
        "report marked failed after worker error",
        extra={"report_id": str(report_id), "reason": reason},
    )
    return True


def reconcile_stale_running_scans(
    db: Session,
    *,
    stale_after_seconds: int,
) -> int:
    """Fail scans left in RUNNING after worker crash or hard timeout."""
    cutoff = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
    stale = (
        db.query(Scan)
        .filter(
            Scan.status == ScanStatus.RUNNING,
            Scan.running_at.isnot(None),
            Scan.running_at < cutoff,
        )
        .all()
    )
    count = 0
    for scan in stale:
        update_scan_status(db, scan, status=ScanStatus.FAILED)
        record_scan_audit(
            db,
            scan,
            action=ScanAuditAction.FAILED,
            extra={"reason": "stale_running_scan"},
        )
        count += 1
        logger.error(
            "reconciled stale running scan",
            extra={"scan_id": str(scan.id), "running_at": scan.running_at.isoformat()},
        )
    return count


def reconcile_stale_generating_reports(
    db: Session,
    *,
    stale_after_seconds: int,
) -> int:
    cutoff = datetime.now(UTC) - timedelta(seconds=stale_after_seconds)
    stale = (
        db.query(Report)
        .filter(
            Report.status == ReportStatus.GENERATING,
            Report.updated_at < cutoff,
        )
        .all()
    )
    count = 0
    for report in stale:
        update_report(db, report, status=ReportStatus.FAILED)
        count += 1
        logger.error(
            "reconciled stale generating report",
            extra={"report_id": str(report.id), "updated_at": report.updated_at.isoformat()},
        )
    return count
