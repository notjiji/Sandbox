from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.organizations.services.activity_service import present_activity_events
from app.findings.enums import FindingStatus
from app.members.models import OrganizationMember
from app.organizations.repositories.overview_repository import (
    ANALYTICS_PERIOD_DAYS,
    count_assets,
    count_assets_since,
    count_critical_findings_change,
    count_findings,
    count_members,
    count_members_since,
    count_projects,
    count_projects_since,
    count_reports,
    count_reports_since,
    count_scans,
    count_scans_since,
    get_risk_score_at_or_before,
    list_recent_activity,
    list_recent_reports,
    list_recent_scans,
)
from app.organizations.schemas_overview import (
    OrganizationAnalytics,
    OrganizationOverview,
    OrganizationStats,
    OrganizationTrends,
    RecentReportSummary,
    RecentScanSummary,
)
from app.risk.service import risk_service


def _build_analytics(
    db: Session,
    *,
    organization_id,
    average_risk: float | None,
    period_days: int = ANALYTICS_PERIOD_DAYS,
) -> OrganizationAnalytics:
    since = datetime.now(UTC) - timedelta(days=period_days)
    previous_risk = get_risk_score_at_or_before(db, organization_id=organization_id, at=since)
    risk_delta = None
    if average_risk is not None and previous_risk is not None:
        risk_delta = round(average_risk - previous_risk, 1)

    return OrganizationAnalytics(
        average_risk=average_risk,
        period_days=period_days,
        trends=OrganizationTrends(
            assets=count_assets_since(db, organization_id=organization_id, since=since),
            members=count_members_since(db, organization_id=organization_id, since=since),
            projects=count_projects_since(db, organization_id=organization_id, since=since),
            scans=count_scans_since(db, organization_id=organization_id, since=since),
            reports=count_reports_since(db, organization_id=organization_id, since=since),
            critical_findings=count_critical_findings_change(
                db,
                organization_id=organization_id,
                since=since,
            ),
            average_risk=risk_delta,
        ),
    )


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
    analytics = _build_analytics(
        db,
        organization_id=org_id,
        average_risk=security.overall_security_score,
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
        analytics=analytics,
        security=security,
        recent_scans=recent_scans,
        recent_reports=recent_reports,
        recent_activity=recent_activity,
    )
