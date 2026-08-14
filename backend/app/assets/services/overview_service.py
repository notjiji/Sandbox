import uuid

from sqlalchemy.orm import Session

from app.assets.repositories.asset_repository import get_asset_by_id
from app.assets.repositories.overview_repository import (
    count_asset_findings,
    count_asset_scans,
    list_asset_activity,
    list_asset_open_findings,
    list_asset_recent_scans,
    list_asset_risk_trend,
    list_project_recent_reports,
)
from app.assets.schemas_overview import AssetOverview, AssetStats
from app.assets.services.asset_enrichment import load_security_stats_batch
from app.assets.services.asset_service import asset_service
from app.audit.schemas import AuditLogSummary
from app.findings.models import Finding
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.services.finding_service import to_finding_summary
from app.members.models import OrganizationMember
from app.organizations.schemas_overview import RecentReportSummary
from app.projects.repositories.overview_repository import count_project_reports
from app.projects.validators import require_active_project
from app.core.exceptions import NotFoundError
from app.risk.repositories.risk_repository import get_latest_asset_risk_for_organization
from app.risk.schemas import AssetRiskResponse, RiskTrendPoint, unscanned_asset_risk
from app.scans.services.scan_service import to_scan_summary


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


def _asset_risk_response(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRiskResponse:
    latest = get_latest_asset_risk_for_organization(
        db,
        organization_id=organization_id,
        asset_id=asset_id,
    )
    if not latest:
        return unscanned_asset_risk(asset_id=str(asset_id))
    return AssetRiskResponse(
        asset_id=str(latest.asset_id),
        scanned=True,
        scan_id=str(latest.scan_id) if latest.scan_id else None,
        total_risk=float(latest.total_risk),
        score=float(latest.score),
        grade=latest.grade,
        critical_count=latest.critical_count,
        high_count=latest.high_count,
        medium_count=latest.medium_count,
        low_count=latest.low_count,
        calculated_at=latest.calculated_at,
    )


def get_asset_overview(
    db: Session,
    membership: OrganizationMember,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetOverview:
    require_active_project(db, membership, project_id)
    asset = get_asset_by_id(
        db,
        project_id=project_id,
        asset_id=asset_id,
        include_deleted=True,
    )
    if not asset:
        raise NotFoundError("Asset")

    open_findings = count_asset_findings(db, asset_id=asset_id, status=FindingStatus.OPEN)
    total_findings = count_asset_findings(db, asset_id=asset_id)
    critical_open = (
        db.query(Finding)
        .filter(
            Finding.asset_id == asset_id,
            Finding.status == FindingStatus.OPEN,
            Finding.severity == FindingSeverity.CRITICAL,
        )
        .count()
    )

    risk = _asset_risk_response(
        db,
        organization_id=membership.organization_id,
        asset_id=asset_id,
    )

    stats = AssetStats(
        scans=count_asset_scans(db, project_id=project_id, asset_id=asset_id),
        open_findings=open_findings,
        total_findings=total_findings,
        critical_findings=critical_open,
        reports=count_project_reports(db, project_id=project_id),
    )

    recent_scans = [
        to_scan_summary(scan)
        for scan in list_asset_recent_scans(db, project_id=project_id, asset_id=asset_id)
    ]
    top_findings = [
        to_finding_summary(finding)
        for finding in list_asset_open_findings(db, asset_id=asset_id)
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
    recent_activity = [
        _to_audit_summary(record)
        for record in list_asset_activity(
            db,
            organization_id=membership.organization_id,
            project_id=project_id,
            asset_id=asset_id,
        )
    ]
    scan_trend = [
        RiskTrendPoint(
            date=row.calculated_at,
            security_score=float(row.score),
            grade=row.grade,
            total_risk=float(row.total_risk),
        )
        for row in list_asset_risk_trend(db, asset_id=asset_id)
    ]

    security_stats = load_security_stats_batch(
        db,
        organization_id=membership.organization_id,
        asset_ids=[asset_id],
    ).get(asset_id)
    asset_summary = asset_service.to_summary(asset, security=security_stats)

    return AssetOverview(
        asset=asset_summary,
        stats=stats,
        risk=risk,
        scan_trend=scan_trend,
        recent_scans=recent_scans,
        top_findings=top_findings,
        recent_reports=recent_reports,
        recent_activity=recent_activity,
    )
