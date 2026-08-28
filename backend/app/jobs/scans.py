"""Background scan execution via Celery."""

import uuid

from celery.exceptions import SoftTimeLimitExceeded

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.scans.services.scan_executor import run_queued_scan
from app.scans.services import schedule_service
from app.scans.services.scan_recovery import (
    fail_running_scan,
    reconcile_stale_generating_reports,
    reconcile_stale_running_scans,
)
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.jobs.scans")


@celery_app.task(
    name="app.jobs.scans.execute_scan",
    bind=True,
    max_retries=0,
    acks_late=True,
    reject_on_worker_lost=True,
)
def execute_scan(
    self,
    *,
    scan_id: str,
    project_id: str,
    asset_id: str,
    correlation_id: str | None = None,
) -> str:
    db = SessionLocal()
    try:
        run_queued_scan(
            db,
            scan_id=uuid.UUID(scan_id),
            project_id=uuid.UUID(project_id),
            asset_id=uuid.UUID(asset_id),
        )
        db.commit()
        return "ok"
    except SoftTimeLimitExceeded:
        db.rollback()
        fail_running_scan(db, scan_id=uuid.UUID(scan_id), reason="scan_task_timeout")
        db.commit()
        logger.error(
            "scan worker soft timeout",
            extra={"scan_id": scan_id, "project_id": project_id, "asset_id": asset_id},
        )
        raise
    except Exception:
        db.rollback()
        logger.exception(
            "scan worker failed",
            extra={"scan_id": scan_id, "project_id": project_id, "asset_id": asset_id},
        )
        raise
    finally:
        db.close()


@celery_app.task(name="app.jobs.scans.check_due_schedules")
def check_due_schedules() -> int:
    db = SessionLocal()
    try:
        return schedule_service.fire_due_schedules(db)
    except Exception:
        db.rollback()
        logger.exception("scan schedule worker failed")
        raise
    finally:
        db.close()


@celery_app.task(name="app.jobs.scans.reconcile_stale_jobs")
def reconcile_stale_jobs() -> dict[str, int]:
    """Fail scans/reports left in-flight after worker crash or timeout."""
    from app.core.config import get_settings

    settings = get_settings()
    db = SessionLocal()
    try:
        scans = reconcile_stale_running_scans(
            db,
            stale_after_seconds=settings.SCAN_STALE_RUNNING_SECONDS,
        )
        reports = reconcile_stale_generating_reports(
            db,
            stale_after_seconds=settings.REPORT_STALE_GENERATING_SECONDS,
        )
        db.commit()
        if scans or reports:
            logger.warning(
                "reconciled stale background jobs",
                extra={"stale_scans": scans, "stale_reports": reports},
            )
        return {"stale_scans": scans, "stale_reports": reports}
    except Exception:
        db.rollback()
        logger.exception("stale job reconciliation failed")
        raise
    finally:
        db.close()
