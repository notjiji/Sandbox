from sqlalchemy.orm import Session

from app.dashboard.repository import (
    count_assets_by_category,
    count_open_findings_by_severity,
    get_latest_scan,
    get_primary_project_id,
    list_top_open_findings,
    list_upcoming_schedules_for_organization,
)
from app.dashboard.schemas import (
    DashboardActivityResponse,
    DashboardAssetsSummary,
    DashboardCriticalFinding,
    DashboardFindingsSummaryResponse,
    DashboardLastScan,
    DashboardOverviewResponse,
    DashboardRiskTrendResponse,
    DashboardScore,
    DashboardTopAsset,
    DashboardTopAssetsResponse,
    DashboardUpcomingScan,
    DashboardUpcomingScansResponse,
)
from app.members.models import OrganizationMember
from app.organizations.repositories.overview_repository import list_recent_activity
from app.organizations.services.activity_service import present_activity_events
from app.risk.repositories.risk_repository import get_previous_organization_score
from app.risk.service import risk_service


def _build_score(db: Session, *, organization_id, metrics) -> DashboardScore:
    current = metrics.overall_security_score
    previous = get_previous_organization_score(db, organization_id=organization_id)
    change = None
    if current is not None and previous is not None:
        change = round(current - previous, 1)
    return DashboardScore(
        current=current,
        previous=previous,
        change=change,
        grade=metrics.organization_grade,
        trend=metrics.trend,
    )


def _build_last_scan(scan) -> DashboardLastScan:
    if scan is None:
        return DashboardLastScan()
    asset = scan.asset
    return DashboardLastScan(
        status=scan.status.value if hasattr(scan.status, "value") else str(scan.status),
        timestamp=scan.completed_at or scan.created_at,
        scan_id=str(scan.id),
        project_id=str(scan.project_id),
        asset_id=str(scan.asset_id),
        asset_name=asset.name if asset else None,
    )


def get_dashboard_overview(
    db: Session,
    membership: OrganizationMember,
) -> DashboardOverviewResponse:
    org_id = membership.organization_id
    metrics = risk_service.get_dashboard_metrics(db, membership)
    org_risk = risk_service.calculate_organization_risk(db, membership, refresh=False)
    asset_counts = count_assets_by_category(db, organization_id=org_id)
    findings = count_open_findings_by_severity(db, organization_id=org_id)
    last_scan = get_latest_scan(db, organization_id=org_id)
    primary_project = get_primary_project_id(db, organization_id=org_id)

    return DashboardOverviewResponse(
        score=_build_score(db, organization_id=org_id, metrics=metrics),
        assets=DashboardAssetsSummary(**asset_counts),
        findings=findings,
        last_scan=_build_last_scan(last_scan),
        primary_project_id=str(primary_project) if primary_project else None,
        scanned_assets=org_risk.scanned_assets,
        unscanned_assets=org_risk.unscanned_assets,
        assets_at_risk=metrics.assets_at_risk,
        trend=metrics.trend,
    )


def get_dashboard_risk_trend(
    db: Session,
    membership: OrganizationMember,
) -> DashboardRiskTrendResponse:
    metrics = risk_service.get_dashboard_metrics(db, membership)
    return DashboardRiskTrendResponse(history=metrics.risk_trend)


def get_dashboard_findings_summary(
    db: Session,
    membership: OrganizationMember,
    *,
    limit: int = 5,
) -> DashboardFindingsSummaryResponse:
    org_id = membership.organization_id
    breakdown = count_open_findings_by_severity(db, organization_id=org_id)
    findings = list_top_open_findings(db, organization_id=org_id, limit=limit)
    top = [
        DashboardCriticalFinding(
            finding_id=str(finding.id),
            finding_code=finding.finding_code or "",
            title=finding.title,
            severity=finding.severity.value
            if hasattr(finding.severity, "value")
            else str(finding.severity),
            risk_score=float(finding.risk_score or 0),
            asset_id=str(finding.asset_id),
            asset_name=finding.asset.name if finding.asset else "",
            project_id=str(finding.project_id),
        )
        for finding in findings
    ]
    return DashboardFindingsSummaryResponse(breakdown=breakdown, top_findings=top)


def get_dashboard_top_assets(
    db: Session,
    membership: OrganizationMember,
    *,
    limit: int = 5,
) -> DashboardTopAssetsResponse:
    import uuid as uuid_lib

    from app.assets.models import Asset

    org_risk = risk_service.calculate_organization_risk(db, membership, refresh=False)
    scored = [
        item
        for item in org_risk.asset_scores
        if item.scanned and item.score is not None
    ]
    scored.sort(key=lambda item: item.score if item.score is not None else 101)
    top_ids = [uuid_lib.UUID(item.asset_id) for item in scored[:limit]]
    assets_by_id: dict[str, Asset] = {}
    if top_ids:
        rows = db.query(Asset).filter(Asset.id.in_(top_ids)).all()
        assets_by_id = {str(asset.id): asset for asset in rows}

    items = []
    for item in scored[:limit]:
        asset = assets_by_id.get(item.asset_id)
        items.append(
            DashboardTopAsset(
                asset_id=item.asset_id,
                asset_name=asset.name if asset else item.asset_id,
                project_id=str(asset.project_id) if asset else "",
                score=item.score,
                grade=item.grade,
                scanned=item.scanned,
            )
        )
    return DashboardTopAssetsResponse(items=items)


def get_dashboard_activity(
    db: Session,
    membership: OrganizationMember,
    *,
    limit: int = 10,
) -> DashboardActivityResponse:
    records = list_recent_activity(
        db,
        organization_id=membership.organization_id,
        limit=limit,
    )
    items = present_activity_events(db, records)
    return DashboardActivityResponse(
        items=[item.model_dump(mode="json") for item in items],
        total=len(items),
    )


def get_dashboard_upcoming_scans(
    db: Session,
    membership: OrganizationMember,
    *,
    limit: int = 10,
) -> DashboardUpcomingScansResponse:
    schedules = list_upcoming_schedules_for_organization(
        db,
        organization_id=membership.organization_id,
        limit=limit,
    )
    items = [
        DashboardUpcomingScan(
            schedule_id=str(schedule.id),
            asset_id=str(schedule.asset_id),
            asset_name=schedule.asset.name if schedule.asset else "",
            project_id=str(schedule.project_id),
            scan_type=schedule.scan_type.value
            if hasattr(schedule.scan_type, "value")
            else str(schedule.scan_type),
            preset=schedule.preset.value
            if hasattr(schedule.preset, "value")
            else str(schedule.preset),
            next_run_at=schedule.next_run_at,
        )
        for schedule in schedules
        if schedule.next_run_at is not None
    ]
    return DashboardUpcomingScansResponse(items=items)
