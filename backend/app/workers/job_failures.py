"""Shared Celery task failure handling and structured logging."""

from __future__ import annotations

import uuid

from celery.exceptions import SoftTimeLimitExceeded

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.scans.services.scan_recovery import fail_generating_report, fail_running_scan

logger = get_logger("sandbox.worker.jobs")

_SCAN_TASK = "app.jobs.scans.execute_scan"
_REPORT_TASK = "app.jobs.reports.generate_report"


def job_type_for_task_name(task_name: str | None) -> str:
    if task_name == _SCAN_TASK:
        return "scan"
    if task_name == _REPORT_TASK:
        return "report"
    if task_name and task_name.startswith("app.jobs.monitoring"):
        return "monitoring"
    if task_name and task_name.startswith("app.jobs.scans"):
        return "scan_schedule"
    return "background"


def log_failed_job(
    *,
    task_id: str,
    task_name: str | None,
    exception: BaseException,
    traceback,
    einfo,
) -> None:
    logger.error(
        "background job failed",
        extra={
            "job_type": job_type_for_task_name(task_name),
            "task_name": task_name,
            "task_id": task_id,
            "exception_type": type(exception).__name__,
            "exception_message": str(exception),
            "timed_out": isinstance(exception, SoftTimeLimitExceeded),
            "stack_trace": str(einfo) if einfo else traceback,
        },
        exc_info=einfo.exc_info if einfo else None,
    )


def recover_failed_job_state(
    *,
    task_name: str | None,
    kwargs: dict,
    exception: BaseException | None = None,
) -> None:
    """Ensure domain rows do not stay RUNNING/GENERATING after task failure."""
    if not task_name:
        return

    timed_out = isinstance(exception, SoftTimeLimitExceeded)
    db = SessionLocal()
    try:
        if task_name == _SCAN_TASK:
            scan_id = kwargs.get("scan_id")
            if scan_id:
                reason = "scan_task_timeout" if timed_out else "scan_task_failed"
                fail_running_scan(db, scan_id=uuid.UUID(str(scan_id)), reason=reason)
        elif task_name == _REPORT_TASK:
            report_id = kwargs.get("report_id")
            if report_id:
                reason = "report_task_timeout" if timed_out else "report_task_failed"
                fail_generating_report(
                    db,
                    report_id=uuid.UUID(str(report_id)),
                    reason=reason,
                )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception(
            "failed to reconcile job state after task failure",
            extra={"task_name": task_name, "task_kwargs": list(kwargs.keys())},
        )
    finally:
        db.close()
