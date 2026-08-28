"""Full report generation pipeline."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.core.report_engine.ai_summary import generate_ai_summary
from app.core.report_engine.data import REPORT_VERSION, collect_report_data
from app.core.report_engine.renderer import write_report_artifacts
from app.reports.enums import ReportStatus
from app.reports.models import Report
from app.reports.repositories.report_repository import update_report


def run_report_pipeline(db: Session, *, report_id: uuid.UUID) -> Report:
    report = (
        db.query(Report)
        .options(joinedload(Report.creator))
        .filter(Report.id == report_id)
        .first()
    )
    if not report:
        raise ValueError("Report not found")

    update_report(db, report, status=ReportStatus.GENERATING)
    db.commit()

    try:
        data = collect_report_data(db, report=report)
        data.ai_summary = generate_ai_summary(data)
        pdf_artifact, _html_artifact, file_size = write_report_artifacts(data)
        update_report(
            db,
            report,
            status=ReportStatus.READY,
            file_url=pdf_artifact.key,
            file_size=file_size,
            completed_at=datetime.now(UTC),
            report_version=REPORT_VERSION,
        )
    except Exception:
        update_report(db, report, status=ReportStatus.FAILED)
        db.commit()
        raise

    db.commit()
    db.refresh(report)
    return report


def preview_report_html(db: Session, *, report: Report) -> str:
    from app.core.report_engine.renderer import render_report_html

    data = collect_report_data(db, report=report)
    if not data.ai_summary:
        data.ai_summary = generate_ai_summary(data)
    return render_report_html(data)
