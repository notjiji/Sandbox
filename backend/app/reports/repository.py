import uuid

from sqlalchemy.orm import Session

from app.reports.enums import ReportStatus
from app.reports.models import Report


def list_reports_for_project(db: Session, *, project_id: uuid.UUID) -> list[Report]:
    return (
        db.query(Report)
        .filter(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
        .all()
    )


def get_report_by_id(
    db: Session,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
) -> Report | None:
    return (
        db.query(Report)
        .filter(Report.id == report_id, Report.project_id == project_id)
        .first()
    )


def create_report(
    db: Session,
    *,
    project_id: uuid.UUID,
    name: str,
    description: str | None = None,
    created_by: uuid.UUID | None = None,
) -> Report:
    report = Report(
        project_id=project_id,
        name=name,
        description=description,
        status=ReportStatus.DRAFT,
        created_by=created_by,
    )
    db.add(report)
    db.flush()
    return report


def update_report(
    db: Session,
    report: Report,
    *,
    name: str | None = None,
    description: str | None = None,
    status: ReportStatus | None = None,
    file_url: str | None = None,
) -> Report:
    if name is not None:
        report.name = name
    if description is not None:
        report.description = description
    if status is not None:
        report.status = status
    if file_url is not None:
        report.file_url = file_url
    db.add(report)
    db.flush()
    return report


def delete_report(db: Session, report: Report) -> None:
    db.delete(report)
