import uuid

from sqlalchemy.orm import Session

from app.audit.schemas import AuditLogSummary
from app.findings.enums import FindingStatus
from app.members.models import OrganizationMember
from app.organizations.schemas_overview import RecentReportSummary, RecentScanSummary
from app.projects.repositories.overview_repository import (
    count_project_assets,
    count_project_findings,
    count_project_reports,
    count_project_scans,
    list_project_activity,
    list_project_recent_reports,
    list_project_recent_scans,
)
from app.projects.schemas_overview import ProjectActivityResponse, ProjectOverview, ProjectStats
from app.projects.services.project_service import to_project_summary
from app.projects.validators import require_active_project
from app.risk.service import risk_service


def _to_audit_summary(record) -> AuditLogSummary:
    return AuditLogSummary(
        id=str(record.id),
        action=record.action,
        user_id=str(record.user_id) if record.user_id else None,
        resource_type=record.resource_type,
        resource_id=str(record.resource_id) if record.resource_id else None,
        entity_type=record.resource_type,
        entity_id=str(record.resource_id) if record.resource_id else None,
        severity=getattr(record, "severity", None) or "info",
        details=record.details,
        created_at=record.created_at,
    )


def get_project_overview(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
) -> ProjectOverview:
    project = require_active_project(db, membership, project_id)
    summary = to_project_summary(project)

    stats = ProjectStats(
        assets=count_project_assets(db, project_id=project_id),
        scans=count_project_scans(db, project_id=project_id),
        open_findings=count_project_findings(
            db, project_id=project_id, status=FindingStatus.OPEN
        ),
        total_findings=count_project_findings(db, project_id=project_id),
        reports=count_project_reports(db, project_id=project_id),
    )

    security = risk_service.calculate_project_risk(
        db, membership, project_id=project_id, refresh=False
    )

    recent_scans = [
        RecentScanSummary(
            id=str(scan.id),
            project_id=str(scan.project_id),
            asset_id=str(scan.asset_id),
            status=scan.status,
            scan_type=scan.scan_type,
            created_at=scan.created_at,
        )
        for scan in list_project_recent_scans(db, project_id=project_id)
    ]

    recent_reports = [
        RecentReportSummary(
            id=str(report.id),
            project_id=str(report.project_id),
            name=report.name,
            status=report.status,
            created_at=report.created_at,
        )
        for report in list_project_recent_reports(db, project_id=project_id)
    ]

    activity_records, _ = list_project_activity(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
        limit=10,
        offset=0,
    )
    recent_activity = [_to_audit_summary(record) for record in activity_records]

    return ProjectOverview(
        project=summary,
        stats=stats,
        security=security,
        recent_scans=recent_scans,
        recent_reports=recent_reports,
        recent_activity=recent_activity,
    )


def get_project_activity(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> ProjectActivityResponse:
    require_active_project(db, membership, project_id)
    offset = (page - 1) * limit
    records, total = list_project_activity(
        db,
        organization_id=membership.organization_id,
        project_id=project_id,
        limit=limit,
        offset=offset,
    )
    return ProjectActivityResponse(
        items=[_to_audit_summary(record) for record in records],
        total=total,
        page=page,
        limit=limit,
    )
