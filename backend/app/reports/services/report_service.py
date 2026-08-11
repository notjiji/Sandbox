import uuid
from pathlib import Path

from sqlalchemy.orm import Session, joinedload

from app.assets.repositories.asset_repository import get_asset_by_id
from app.audit.service import record_audit_event
from app.core.config import get_settings
from app.core.exceptions import NotFoundError, ValidationAppError
from app.core.report_engine.generator import REPORT_TYPE_LABELS
from app.core.report_engine.pipeline import preview_report_html, run_report_pipeline
from app.core.report_engine.renderer import report_file_path
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.reports.enums import ReportStatus, ReportType
from app.reports.events import ReportAuditAction
from app.reports.models import Report
from app.reports.repositories.report_repository import (
    create_report,
    delete_report,
    get_asset_report_by_id,
    get_report_by_id,
    list_reports_for_asset_paginated,
    list_reports_for_organization_paginated,
    list_reports_for_project_paginated,
    update_report,
)
from app.reports.schemas import (
    CreateAssetReportRequest,
    CreateReportRequest,
    ReportListQuery,
    ReportListResponse,
    ReportSummary,
    UpdateReportRequest,
)


def to_report_summary(report: Report) -> ReportSummary:
    creator_name = None
    if report.creator:
        creator_name = f"{report.creator.first_name} {report.creator.last_name}".strip()
    project_name = report.project.name if getattr(report, "project", None) else None
    return ReportSummary(
        id=str(report.id),
        project_id=str(report.project_id),
        project_name=project_name,
        asset_id=str(report.asset_id) if report.asset_id else None,
        scan_id=str(report.scan_id) if report.scan_id else None,
        report_type=report.report_type,
        report_version=report.report_version,
        name=report.name,
        description=report.description,
        status=report.status,
        file_url=report.file_url,
        file_size=report.file_size,
        created_by=str(report.created_by) if report.created_by else None,
        created_by_name=creator_name,
        created_at=report.created_at,
        updated_at=report.updated_at,
        completed_at=report.completed_at,
    )


def _hydrate_report(db: Session, report: Report) -> Report:
    hydrated = (
        db.query(Report)
        .options(joinedload(Report.creator))
        .filter(Report.id == report.id)
        .first()
    )
    return hydrated or report


def _default_report_name(report_type: ReportType, *, asset_name: str | None = None) -> str:
    label = REPORT_TYPE_LABELS.get(report_type, report_type.value.title())
    if asset_name:
        return f"{label} — {asset_name}"
    return f"{label} Report"


def _parse_scan_id(raw: str | None) -> uuid.UUID | None:
    if not raw:
        return None
    try:
        return uuid.UUID(raw)
    except ValueError as exc:
        raise ValidationAppError("Invalid scan_id") from exc


def _queue_generation(report_id: uuid.UUID) -> None:
    from app.jobs.reports import generate_report_task

    generate_report_task.delay(report_id=str(report_id))


def _start_generation(
    db: Session,
    membership: OrganizationMember,
    report: Report,
    *,
    audit_action: str = ReportAuditAction.GENERATE,
) -> ReportSummary:
    if report.status == ReportStatus.GENERATING:
        raise ValidationAppError("Report generation is already in progress")

    update_report(db, report, status=ReportStatus.GENERATING)
    record_audit_event(
        db,
        action=audit_action,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
        details={"project_id": str(report.project_id), "report_type": report.report_type.value},
    )
    db.commit()
    db.refresh(report)

    if get_settings().REPORT_RUN_INLINE:
        try:
            run_report_pipeline(db, report_id=report.id)
            db.commit()
            db.refresh(report)
        except Exception as exc:
            raise ValidationAppError("Report generation failed") from exc
    else:
        _queue_generation(report.id)

    return to_report_summary(_hydrate_report(db, report))


def list_project_reports(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    query: ReportListQuery | None = None,
) -> ReportListResponse:
    require_active_project(db, membership, project_id)
    params = query or ReportListQuery()
    reports, total = list_reports_for_project_paginated(
        db, project_id=project_id, query=params
    )
    items = [to_report_summary(report) for report in reports]
    return ReportListResponse(items=items, total=total, page=params.page, limit=params.limit)


def list_asset_reports(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    query: ReportListQuery | None = None,
) -> ReportListResponse:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(
        db,
        project_id=project_id,
        asset_id=asset_id,
        include_deleted=True,
    )
    if not asset:
        raise NotFoundError("Asset")

    params = query or ReportListQuery()
    reports, total = list_reports_for_asset_paginated(
        db,
        project_id=project_id,
        asset_id=asset_id,
        query=params,
    )
    items = [to_report_summary(report) for report in reports]
    return ReportListResponse(items=items, total=total, page=params.page, limit=params.limit)


def list_organization_reports(
    db: Session,
    membership: OrganizationMember,
    *,
    query: ReportListQuery | None = None,
) -> ReportListResponse:
    params = query or ReportListQuery()
    reports, total = list_reports_for_organization_paginated(
        db,
        organization_id=membership.organization_id,
        query=params,
    )
    items = [to_report_summary(report) for report in reports]
    return ReportListResponse(items=items, total=total, page=params.page, limit=params.limit)


def create_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    body: CreateReportRequest,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    name = body.name or _default_report_name(body.report_type)
    asset_id = uuid.UUID(body.asset_id) if body.asset_id else None
    report = create_report(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=_parse_scan_id(body.scan_id),
        name=name,
        description=body.description,
        created_by=membership.user_id,
        report_type=body.report_type,
    )
    record_audit_event(
        db,
        action=ReportAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
        details={
            "project_id": str(project_id),
            "name": report.name,
            "report_type": body.report_type.value,
        },
    )
    db.commit()
    db.refresh(report)

    if body.generate:
        return _start_generation(db, membership, report)
    return to_report_summary(_hydrate_report(db, report))


def create_asset_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    body: CreateAssetReportRequest,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(
        db,
        project_id=project_id,
        asset_id=asset_id,
        include_deleted=True,
    )
    if not asset:
        raise NotFoundError("Asset")

    name = body.name or _default_report_name(body.report_type, asset_name=asset.name)
    report = create_report(
        db,
        project_id=project_id,
        asset_id=asset_id,
        scan_id=_parse_scan_id(body.scan_id),
        name=name,
        description=body.description,
        created_by=membership.user_id,
        report_type=body.report_type,
    )
    record_audit_event(
        db,
        action=ReportAuditAction.CREATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
        details={
            "project_id": str(project_id),
            "asset_id": str(asset_id),
            "name": report.name,
            "report_type": body.report_type.value,
        },
    )
    db.commit()
    db.refresh(report)

    if body.generate:
        return _start_generation(db, membership, report)
    return to_report_summary(_hydrate_report(db, report))


def get_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
) -> ReportSummary:
    require_active_project(db, membership, project_id)
    report = (
        db.query(Report)
        .options(joinedload(Report.creator))
        .filter(Report.id == report_id, Report.project_id == project_id)
        .first()
    )
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
    return _start_generation(db, membership, report)


def regenerate_project_report(
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
    return _start_generation(
        db,
        membership,
        report,
        audit_action=ReportAuditAction.REGENERATE,
    )


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

    _remove_report_file(report.id)
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


def preview_project_report(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    asset_id: uuid.UUID | None = None,
) -> str:
    require_active_project(db, membership, project_id)
    if asset_id is not None:
        report = get_asset_report_by_id(
            db,
            project_id=project_id,
            asset_id=asset_id,
            report_id=report_id,
        )
    else:
        report = get_report_by_id(db, project_id=project_id, report_id=report_id)
    if not report:
        raise NotFoundError("Report")
    return preview_report_html(db, report=report)


def resolve_report_download(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    report_id: uuid.UUID,
    asset_id: uuid.UUID | None = None,
) -> tuple[Report, Path]:
    require_active_project(db, membership, project_id)
    if asset_id is not None:
        report = get_asset_report_by_id(
            db,
            project_id=project_id,
            asset_id=asset_id,
            report_id=report_id,
        )
    else:
        report = get_report_by_id(db, project_id=project_id, report_id=report_id)
    if not report:
        raise NotFoundError("Report")
    if report.status != ReportStatus.READY:
        raise ValidationAppError("Report is not ready for download")

    path = report_file_path(report.id)
    if not path.exists():
        run_report_pipeline(db, report_id=report.id)
        db.commit()
        path = report_file_path(report.id)

    record_audit_event(
        db,
        action=ReportAuditAction.DOWNLOAD,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="report",
        resource_id=report.id,
        details={"project_id": str(project_id)},
    )
    db.commit()
    return report, path


def _remove_report_file(report_id: uuid.UUID) -> None:
    for ext in ("pdf", "html"):
        path = report_file_path(report_id, ext=ext)
        if path.exists():
            path.unlink()
