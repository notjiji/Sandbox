import uuid

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session

from app.reports.enums import ReportStatus, ReportType
from app.reports.models import Report
from app.reports.schemas import ReportListQuery


def list_reports_for_project(db: Session, *, project_id: uuid.UUID) -> list[Report]:
    return (
        db.query(Report)
        .filter(Report.project_id == project_id, Report.asset_id.is_(None))
        .order_by(Report.created_at.desc())
        .all()
    )


def list_reports_for_asset_paginated(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    query: ReportListQuery,
) -> tuple[list[Report], int]:
    base = db.query(Report).filter(
        Report.project_id == project_id,
        Report.asset_id == asset_id,
    )

    if query.report_type is not None:
        base = base.filter(Report.report_type == query.report_type)
    if query.status is not None:
        base = base.filter(Report.status == query.status)
    if query.search:
        needle = f"%{query.search.strip().lower()}%"
        base = base.filter(
            or_(
                func.lower(Report.name).like(needle),
                func.lower(Report.description).like(needle),
                cast(Report.report_type, String).ilike(needle),
            )
        )

    total = base.count()
    offset = (query.page - 1) * query.limit
    items = (
        base.order_by(Report.created_at.desc())
        .offset(offset)
        .limit(query.limit)
        .all()
    )
    return items, int(total)


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


def get_asset_report_by_id(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    report_id: uuid.UUID,
) -> Report | None:
    return (
        db.query(Report)
        .filter(
            Report.id == report_id,
            Report.project_id == project_id,
            Report.asset_id == asset_id,
        )
        .first()
    )


def create_report(
    db: Session,
    *,
    project_id: uuid.UUID,
    name: str,
    description: str | None = None,
    created_by: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    report_type: ReportType = ReportType.EXECUTIVE,
) -> Report:
    report = Report(
        project_id=project_id,
        asset_id=asset_id,
        report_type=report_type,
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
