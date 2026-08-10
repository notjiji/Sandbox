"""Generate reports via the structured pipeline."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.core.report_engine.pipeline import run_report_pipeline
from app.core.report_engine.renderer import report_file_path
from app.reports.models import Report

from app.reports.enums import ReportType

REPORT_TYPE_LABELS = {
    ReportType.EXECUTIVE: "Executive",
    ReportType.TECHNICAL: "Technical",
    ReportType.WEEKLY: "Weekly",
    ReportType.MONTHLY: "Monthly",
}


def generate_report_file(db: Session, *, report: Report) -> uuid.UUID:
    updated = run_report_pipeline(db, report_id=report.id)
    return updated.id
