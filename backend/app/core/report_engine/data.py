"""Normalized report data — separate from presentation."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import Field
from sqlalchemy.orm import Session

from app.assets.enums import AssetType
from app.assets.models import Asset
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.organizations.models import Organization
from app.projects.models import Project
from app.reports.enums import ReportType
from app.reports.models import Report
from app.organizations.settings_defaults import merge_organization_settings
from app.risk.repositories.risk_repository import (
    get_latest_asset_risk,
    get_previous_organization_score,
    list_organization_risk_history,
)
from app.risk.schemas import SeverityBreakdown
from app.scans.models import Scan, ScanPluginRun
from app.shared.schemas.base import BaseSchema

REPORT_VERSION = 1

WEBSITE_TYPES = frozenset({AssetType.WEBSITE, AssetType.API_ENDPOINT})
DOMAIN_TYPES = frozenset({AssetType.DOMAIN, AssetType.EMAIL_DOMAIN})
IP_TYPES = frozenset({AssetType.PUBLIC_IP})
SERVER_TYPES = frozenset({AssetType.SERVER, AssetType.WINDOWS_SERVER, AssetType.DOCKER_HOST})


class ReportBranding(BaseSchema):
    organization_name: str
    logo_url: str | None = None
    primary_color: str = "#7c3aed"
    contact_email: str | None = None
    footer_text: str | None = None


class ReportOrganization(BaseSchema):
    id: str
    name: str
    slug: str


class ReportProject(BaseSchema):
    id: str
    name: str


class ReportScanInfo(BaseSchema):
    id: str
    scan_type: str
    status: str
    completed_at: datetime | None = None


class ReportScore(BaseSchema):
    current: float | None = None
    previous: float | None = None
    change: float | None = None
    grade: str | None = None
    risk_level: str | None = None
    trend: str = "stable"


class ReportAssetSummary(BaseSchema):
    id: str
    name: str
    asset_type: str
    score: float | None = None
    grade: str | None = None
    open_findings: int = 0


class ReportAssetCounts(BaseSchema):
    total: int = 0
    websites: int = 0
    domains: int = 0
    ips: int = 0
    servers: int = 0


class ReportScannerResult(BaseSchema):
    plugin_name: str
    status: str
    findings_count: int = 0
    duration_seconds: float | None = None
    error_message: str | None = None
    metadata_summary: str | None = None


class ReportFinding(BaseSchema):
    id: str
    asset_id: str
    asset_name: str
    plugin: str | None = None
    finding_code: str | None = None
    title: str
    severity: str
    description: str | None = None
    evidence: str | None = None
    impact: str | None = None
    recommendation: str | None = None
    risk_score: float = 0.0
    first_detected: datetime | None = None
    last_detected: datetime | None = None


class ReportData(BaseSchema):
    report_id: str
    report_type: ReportType
    report_version: int = REPORT_VERSION
    title: str
    assessment_date: datetime
    organization: ReportOrganization
    project: ReportProject
    scan: ReportScanInfo | None = None
    branding: ReportBranding
    score: ReportScore
    severity_distribution: SeverityBreakdown
    asset_counts: ReportAssetCounts
    assets: list[ReportAssetSummary] = Field(default_factory=list)
    findings: list[ReportFinding] = Field(default_factory=list)
    key_risks: list[ReportFinding] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    findings_by_plugin: dict[str, int] = Field(default_factory=dict)
    scanner_results: list[ReportScannerResult] = Field(default_factory=list)
    trend_points: list[dict] = Field(default_factory=list)
    ai_summary: str | None = None
    generated_by: str | None = None


def _resolve_branding(organization: Organization) -> ReportBranding:
    merged = merge_organization_settings(getattr(organization, "settings", None) or {})
    branding_settings = merged.get("branding", {})
    contact_email = branding_settings.get("contact_email")
    return ReportBranding(
        organization_name=organization.name,
        logo_url=getattr(organization, "logo_url", None),
        primary_color=branding_settings.get("primary_color") or "#7c3aed",
        contact_email=contact_email,
        footer_text=branding_settings.get("footer_text"),
    )


def _collect_scanner_results(db: Session, *, scan_id: uuid.UUID) -> list[ReportScannerResult]:
    plugin_runs = (
        db.query(ScanPluginRun)
        .filter(ScanPluginRun.scan_id == scan_id)
        .order_by(ScanPluginRun.plugin_name.asc())
        .all()
    )
    results: list[ReportScannerResult] = []
    for run in plugin_runs:
        metadata_summary = None
        if run.metadata_json:
            parts = []
            for key, value in run.metadata_json.items():
                if value is None:
                    continue
                if isinstance(value, (dict, list)):
                    parts.append(f"{key}: {len(value)} item(s)")
                else:
                    text = str(value)
                    parts.append(f"{key}: {text[:120]}")
            metadata_summary = "; ".join(parts[:6]) if parts else None
        results.append(
            ReportScannerResult(
                plugin_name=run.plugin_name,
                status=run.status.value if hasattr(run.status, "value") else str(run.status),
                findings_count=int(run.findings_count or 0),
                duration_seconds=run.duration_seconds,
                error_message=run.error_message,
                metadata_summary=metadata_summary,
            )
        )
    return results


def _severity_breakdown(findings: list[Finding]) -> SeverityBreakdown:
    breakdown = SeverityBreakdown()
    for finding in findings:
        key = finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity)
        if key == "critical":
            breakdown.critical += 1
        elif key == "high":
            breakdown.high += 1
        elif key == "medium":
            breakdown.medium += 1
        elif key == "low":
            breakdown.low += 1
        elif key == "info":
            breakdown.info += 1
    return breakdown


def _asset_counts(assets: list[Asset]) -> ReportAssetCounts:
    counts = ReportAssetCounts(total=len(assets))
    for asset in assets:
        if asset.type in WEBSITE_TYPES:
            counts.websites += 1
        elif asset.type in DOMAIN_TYPES:
            counts.domains += 1
        elif asset.type in IP_TYPES:
            counts.ips += 1
        elif asset.type in SERVER_TYPES:
            counts.servers += 1
    return counts


def _resolve_scan(db: Session, *, report: Report, project_id: uuid.UUID) -> Scan | None:
    if report.scan_id:
        return (
            db.query(Scan)
            .filter(Scan.id == report.scan_id, Scan.project_id == project_id)
            .first()
        )
    query = db.query(Scan).filter(Scan.project_id == project_id)
    if report.asset_id:
        query = query.filter(Scan.asset_id == report.asset_id)
    return query.order_by(Scan.completed_at.desc().nullslast(), Scan.created_at.desc()).first()


def collect_report_data(db: Session, *, report: Report) -> ReportData:
    project = db.query(Project).filter(Project.id == report.project_id).first()
    if not project:
        raise ValueError("Project not found")

    organization = db.query(Organization).filter(Organization.id == project.organization_id).first()
    if not organization:
        raise ValueError("Organization not found")

    scan = _resolve_scan(db, report=report, project_id=report.project_id)

    assets_query = db.query(Asset).filter(
        Asset.project_id == report.project_id,
        Asset.deleted_at.is_(None),
    )
    if report.asset_id:
        assets_query = assets_query.filter(Asset.id == report.asset_id)
    assets = assets_query.order_by(Asset.name.asc()).all()
    assets_by_id = {asset.id: asset for asset in assets}

    findings_query = (
        db.query(Finding)
        .filter(
            Finding.project_id == report.project_id,
            Finding.status == FindingStatus.OPEN,
        )
    )
    if report.asset_id:
        findings_query = findings_query.filter(Finding.asset_id == report.asset_id)
    if scan:
        findings_query = findings_query.filter(Finding.scan_id == scan.id)
    findings = findings_query.order_by(Finding.risk_score.desc()).all()

    plugin_counts: dict[str, int] = {}
    for finding in findings:
        plugin = finding.plugin or "other"
        plugin_counts[plugin] = plugin_counts.get(plugin, 0) + 1

    report_findings = [
        ReportFinding(
            id=str(f.id),
            asset_id=str(f.asset_id),
            asset_name=assets_by_id[f.asset_id].name if f.asset_id in assets_by_id else "",
            plugin=f.plugin,
            finding_code=f.finding_code,
            title=f.title,
            severity=f.severity.value if hasattr(f.severity, "value") else str(f.severity),
            description=f.description,
            evidence=f.evidence,
            impact=f.description,
            recommendation=f.recommendation,
            risk_score=float(f.risk_score or 0),
            first_detected=f.detected_at or f.created_at,
            last_detected=f.updated_at,
        )
        for f in findings
    ]

    key_risks = [
        f
        for f in report_findings
        if f.severity in {"critical", "high"}
    ][:5]

    recommendations: list[str] = []
    seen: set[str] = set()
    for finding in report_findings:
        if finding.recommendation and finding.recommendation not in seen:
            recommendations.append(finding.recommendation)
            seen.add(finding.recommendation)
        if len(recommendations) >= 5:
            break

    asset_summaries: list[ReportAssetSummary] = []
    scores: list[float] = []
    for asset in assets:
        risk = get_latest_asset_risk(db, asset_id=asset.id)
        open_count = sum(1 for f in findings if f.asset_id == asset.id)
        score = float(risk.score) if risk and risk.score is not None else None
        if score is not None:
            scores.append(score)
        asset_summaries.append(
            ReportAssetSummary(
                id=str(asset.id),
                name=asset.name,
                asset_type=asset.type.value if hasattr(asset.type, "value") else str(asset.type),
                score=score,
                grade=risk.grade if risk else None,
                open_findings=open_count,
            )
        )

    current_score = round(sum(scores) / len(scores), 1) if scores else None
    previous_score = get_previous_organization_score(db, organization_id=organization.id)
    change = None
    if current_score is not None and previous_score is not None:
        change = round(current_score - previous_score, 1)

    history = list_organization_risk_history(db, organization_id=organization.id, limit=12)
    trend_points = [
        {
            "date": entry.calculated_at.strftime("%b %Y"),
            "score": float(entry.overall_score),
        }
        for entry in history
    ]

    grade = None
    if current_score is not None:
        if current_score >= 90:
            grade = "A"
        elif current_score >= 80:
            grade = "B"
        elif current_score >= 70:
            grade = "C"
        elif current_score >= 60:
            grade = "D"
        else:
            grade = "F"

    creator_name = None
    if report.created_by and report.creator:
        creator_name = f"{report.creator.first_name} {report.creator.last_name}".strip()

    return ReportData(
        report_id=str(report.id),
        report_type=report.report_type,
        report_version=report.report_version or REPORT_VERSION,
        title=report.name,
        assessment_date=scan.completed_at if scan and scan.completed_at else datetime.now(UTC),
        organization=ReportOrganization(
            id=str(organization.id),
            name=organization.name,
            slug=organization.slug,
        ),
        project=ReportProject(id=str(project.id), name=project.name),
        scan=(
            ReportScanInfo(
                id=str(scan.id),
                scan_type=scan.scan_type.value if hasattr(scan.scan_type, "value") else str(scan.scan_type),
                status=scan.status.value if hasattr(scan.status, "value") else str(scan.status),
                completed_at=scan.completed_at,
            )
            if scan
            else None
        ),
        branding=_resolve_branding(organization),
        score=ReportScore(
            current=current_score,
            previous=previous_score,
            change=change,
            grade=grade,
            trend="improving" if change and change > 0 else "declining" if change and change < 0 else "stable",
        ),
        severity_distribution=_severity_breakdown(findings),
        asset_counts=_asset_counts(assets),
        assets=asset_summaries,
        findings=report_findings,
        key_risks=key_risks,
        recommendations=recommendations,
        findings_by_plugin=plugin_counts,
        scanner_results=_collect_scanner_results(db, scan_id=scan.id) if scan else [],
        trend_points=trend_points,
        generated_by=creator_name,
    )
