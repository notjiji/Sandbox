from sqlalchemy.orm import Session

from app.organizations.services.activity_service import get_organization_activity, present_activity_events
from app.findings.enums import FindingStatus
from app.members.models import OrganizationMember
from app.organizations.repositories.overview_repository import (
    count_assets,
    count_findings,
    count_members,
    count_projects,
    count_reports,
    count_scans,
    list_recent_activity,
    list_recent_reports,
    list_recent_scans,
)
from app.organizations.schemas_overview import (
    OrganizationOverview,
    OrganizationStats,
    RecentReportSummary,
    RecentScanSummary,
)
from app.risk.service import risk_service


def get_organization_overview(
    db: Session,
    membership: OrganizationMember,
) -> OrganizationOverview:
    org_id = membership.organization_id

    stats = OrganizationStats(
        projects=count_projects(db, organization_id=org_id),
        assets=count_assets(db, organization_id=org_id),
        members=count_members(db, organization_id=org_id),
        scans=count_scans(db, organization_id=org_id),
        open_findings=count_findings(db, organization_id=org_id, status=FindingStatus.OPEN),
        total_findings=count_findings(db, organization_id=org_id),
        reports=count_reports(db, organization_id=org_id),
    )

    security = risk_service.get_dashboard_metrics(db, membership)

    recent_scans = [
        RecentScanSummary(
            id=str(scan.id),
            project_id=str(scan.project_id),
            asset_id=str(scan.asset_id),
            status=scan.status,
            scan_type=scan.scan_type,
            created_at=scan.created_at,
        )
        for scan in list_recent_scans(db, organization_id=org_id)
    ]

    recent_reports = [
        RecentReportSummary(
            id=str(report.id),
            project_id=str(report.project_id),
            name=report.name,
            status=report.status,
            created_at=report.created_at,
        )
        for report in list_recent_reports(db, organization_id=org_id)
    ]

    activity_records = list_recent_activity(db, organization_id=org_id)
    recent_activity = present_activity_events(db, activity_records)

    return OrganizationOverview(
        stats=stats,
        security=security,
        recent_scans=recent_scans,
        recent_reports=recent_reports,
        recent_activity=recent_activity,
    )
