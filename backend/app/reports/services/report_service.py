import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationAppError
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.reports.enums import ReportStatus
from app.reports.events import ReportAuditAction
from app.reports.models import Report
from app.reports.repositories.report_repository import (
    create_report,
    delete_report,
    get_report_by_id,
    list_reports_for_project,
    update_report,
)
from app.reports.schemas import CreateReportRequest, ReportListResponse, ReportSummary, UpdateReportRequest
from app.audit.service import record_audit_event


def to_report_summary(report: Report) -> ReportSummary:
    return ReportSummary(
        id=str(report.id),
        project_id=str(report.project_id),
        name=report.name,
        description=report.description,
        status=report.status,
        file_url=report.file_url,
        created_by=str(report.created_by) if report.created_by else None,
    )


def list_project_reports(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> ReportListResponse:
    require_active_project(db, membership, project_id)
    reports = list_reports_for_project(db, project_id=project_id)
    items = [to_report_summary(report) for report in reports]
    return ReportListResponse(items=items, total=len(items))


def create_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: CreateReportRequest,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    report = create_report(
        db,
        project_id=project_id,
        name=body.name,
        description=body.description,
        created_by=membership.user_id,
    )
    record_audit_event(
        db,
        action=ReportAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
        details={"project_id": str(project_id), "name": report.name},
    )
    db.commit()
    db.refresh(report)
    return to_report_summary(report)


def get_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    report = get_report_by_id(db, project_id=project_id, report_id=report_id)
    if not report:
        raise NotFoundError("Report")
    return to_report_summary(report)


def update_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    body: UpdateReportRequest,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    report = get_report_by_id(db, project_id=project_id, report_id=report_id)
    if not report:
        raise NotFoundError("Report")
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")

    update_report(db, report, name=body.name, description=body.description)
    record_audit_event(
        db,
        action=ReportAuditAction.UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
        details=body.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(report)
    return to_report_summary(report)


def generate_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    report = get_report_by_id(db, project_id=project_id, report_id=report_id)
    if not report:
        raise NotFoundError("Report")
    if report.status == ReportStatus.GENERATING:
        raise ValidationAppError("Report generation is already in progress")

    update_report(db, report, status=ReportStatus.GENERATING)
    record_audit_event(
        db,
        action=ReportAuditAction.GENERATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
    )
    db.commit()
    db.refresh(report)
    return to_report_summary(report)


def delete_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
) -> None:
    require_active_project(db, membership, project_id)
    report = get_report_by_id(db, project_id=project_id, report_id=report_id)
    if not report:
        raise NotFoundError("Report")

    delete_report(db, report)
    record_audit_event(
        db,
        action=ReportAuditAction.DELETE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
    )
    db.commit()
