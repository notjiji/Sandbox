"""Background report generation via Celery."""

from __future__ import annotations

import uuid

from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.core.report_engine.pipeline import run_report_pipeline
from app.workers.celery_app import celery_app

logger = get_logger("sandbox.jobs.reports")


@celery_app.task(name="app.jobs.reports.generate_report", bind=True, max_retries=1)
def generate_report_task(self, *, report_id: str) -> str:
    db = SessionLocal()
    try:
        run_report_pipeline(db, report_id=uuid.UUID(report_id))
        db.commit()
        return "ok"
    except Exception:
        db.rollback()
        logger.exception("report worker failed", extra={"report_id": report_id})
        raise
    finally:
        db.close()
