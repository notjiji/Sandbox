"""Background scan execution via Celery."""

import uuid

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.scans.services.scan_executor import run_queued_scan
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.jobs.scans")


@celery_app.task(name="app.jobs.scans.execute_scan", bind=True, max_retries=0)
def execute_scan(
    self,
    *,
    scan_id: str,
    project_id: str,
    asset_id: str,
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
    except Exception:
        db.rollback()
        logger.exception(
            "scan worker failed",
            extra={"scan_id": scan_id, "project_id": project_id, "asset_id": asset_id},
        )
        raise
    finally:
        db.close()
