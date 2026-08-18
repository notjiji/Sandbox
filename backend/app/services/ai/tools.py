"""Internal data tools — AI service reads scan results from PostgreSQL only."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import String, cast, func, or_
from sqlalchemy.orm import Session, joinedload

from app.assets.models import Asset
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.repositories.finding_repository import list_findings_for_scan
from app.projects.models import Project
from app.reports.repositories.report_repository import list_reports_for_project
from app.risk.repositories.risk_repository import (
    get_latest_asset_risk_for_organization,
    get_organization_risk,
)
from app.scans.enums import ScanStatus
from app.scans.repositories.scan_repository import list_scans_for_asset
from app.services.ai.models import (
    AssetContextSnapshot,
    FindingContext,
    ScanContextSnapshot,
)


def _finding_to_context(finding: Finding) -> FindingContext:
    refs = finding.references if isinstance(finding.references, list) else []
    return FindingContext(
        id=str(finding.id),
        plugin=finding.plugin,
        finding_code=finding.finding_code,
        severity=finding.severity.value if hasattr(finding.severity, "value") else str(finding.severity),
        title=finding.title,
        description=finding.description,
        evidence=finding.evidence,
        recommendation=finding.recommendation,
        risk_score=float(finding.risk_score or 0),
        status=finding.status.value if hasattr(finding.status, "value") else str(finding.status),
        references=[str(item) for item in refs],
    )


def get_asset(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> Asset | None:
    return (
        db.query(Asset)
        .filter(Asset.id == asset_id, Asset.organization_id == organization_id, Asset.deleted_at.is_(None))
        .first()
    )


def get_latest_scan(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> ScanContextSnapshot | None:
    scans = list_scans_for_asset(db, project_id=project_id, asset_id=asset_id)
    completed = next((scan for scan in scans if scan.status == ScanStatus.COMPLETED), None)
    if completed is None:
        return None
    findings = list_findings_for_scan(db, project_id=project_id, scan_id=completed.id)
    return ScanContextSnapshot(
        scan_id=str(completed.id),
        scan_date=(completed.completed_at or completed.created_at).isoformat()
        if (completed.completed_at or completed.created_at)
        else None,
        scan_type=completed.scan_type.value if hasattr(completed.scan_type, "value") else str(completed.scan_type),
        status=completed.status.value if hasattr(completed.status, "value") else str(completed.status),
        findings_count=len(findings),
    )


def get_findings_for_scan(
    db: Session,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    open_only: bool = True,
) -> list[FindingContext]:
    findings = list_findings_for_scan(db, project_id=project_id, scan_id=scan_id)
    if open_only:
        findings = [item for item in findings if item.status in (FindingStatus.OPEN, FindingStatus.IN_REVIEW)]
    return [_finding_to_context(item) for item in findings]


def get_risk_score(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> float | None:
    row = get_latest_asset_risk_for_organization(db, organization_id=organization_id, asset_id=asset_id)
    return float(row.score) if row is not None else None


def get_scan_history(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 10,
) -> list[ScanContextSnapshot]:
    scans = list_scans_for_asset(db, project_id=project_id, asset_id=asset_id)[:limit]
    snapshots: list[ScanContextSnapshot] = []
    for scan in scans:
        findings = list_findings_for_scan(db, project_id=project_id, scan_id=scan.id)
        snapshots.append(
            ScanContextSnapshot(
                scan_id=str(scan.id),
                scan_date=(scan.completed_at or scan.created_at).isoformat()
                if (scan.completed_at or scan.created_at)
                else None,
                scan_type=scan.scan_type.value if hasattr(scan.scan_type, "value") else str(scan.scan_type),
                status=scan.status.value if hasattr(scan.status, "value") else str(scan.status),
                findings_count=len(findings),
            )
        )
    return snapshots


def get_organization_summary(db: Session, *, organization_id: uuid.UUID) -> dict:
    org_risk = get_organization_risk(db, organization_id=organization_id)
    open_findings = (
        db.query(func.count(Finding.id))
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.status.in_((FindingStatus.OPEN, FindingStatus.IN_REVIEW)),
        )
        .scalar()
        or 0
    )
    critical_findings = (
        db.query(func.count(Finding.id))
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.status.in_((FindingStatus.OPEN, FindingStatus.IN_REVIEW)),
            Finding.severity == FindingSeverity.CRITICAL,
        )
        .scalar()
        or 0
    )
    asset_count = (
        db.query(func.count(Asset.id))
        .filter(Asset.organization_id == organization_id, Asset.deleted_at.is_(None))
        .scalar()
        or 0
    )
    return {
        "assets": int(asset_count),
        "open_findings": int(open_findings),
        "critical_findings": int(critical_findings),
        "security_score": float(org_risk.security_score) if org_risk else None,
        "risk_level": org_risk.risk_level if org_risk else None,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def search_findings(
    db: Session,
    *,
    organization_id: uuid.UUID,
    keyword: str,
    limit: int = 20,
) -> list[FindingContext]:
    needle = f"%{keyword.strip().lower()}%"
    rows = (
        db.query(Finding)
        .join(Project, Finding.project_id == Project.id)
        .options(joinedload(Finding.asset))
        .filter(
            Project.organization_id == organization_id,
            Finding.status.in_((FindingStatus.OPEN, FindingStatus.IN_REVIEW)),
            or_(
                func.lower(Finding.title).like(needle),
                func.lower(Finding.finding_code).like(needle),
                func.lower(Finding.description).like(needle),
                cast(Finding.plugin, String).ilike(needle),
            ),
        )
        .order_by(Finding.risk_score.desc())
        .limit(limit)
        .all()
    )
    return [_finding_to_context(item) for item in rows]


def get_reports_summary(db: Session, *, organization_id: uuid.UUID, limit: int = 10) -> list[dict]:
    projects = db.query(Project).filter(Project.organization_id == organization_id, Project.is_active.is_(True)).all()
    reports: list[dict] = []
    for project in projects:
        for report in list_reports_for_project(db, project_id=project.id)[:limit]:
            reports.append(
                {
                    "report_id": str(report.id),
                    "project_id": str(project.id),
                    "title": report.title,
                    "created_at": report.created_at.isoformat() if report.created_at else None,
                }
            )
            if len(reports) >= limit:
                return reports
    return reports


def build_asset_snapshot(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset: Asset,
) -> AssetContextSnapshot:
    latest = get_latest_scan(db, project_id=asset.project_id, asset_id=asset.id)
    risk = get_risk_score(db, organization_id=organization_id, asset_id=asset.id)
    open_count = (
        db.query(func.count(Finding.id))
        .filter(
            Finding.asset_id == asset.id,
            Finding.status.in_((FindingStatus.OPEN, FindingStatus.IN_REVIEW)),
        )
        .scalar()
        or 0
    )
    if latest is not None and risk is not None:
        latest = latest.model_copy(update={"risk_score": risk})
    return AssetContextSnapshot(
        asset_id=str(asset.id),
        name=asset.name,
        identifier=asset.external_identifier or asset.name,
        asset_type=asset.type.value if hasattr(asset.type, "value") else str(asset.type),
        latest_scan=latest,
        risk_score=risk,
        open_findings_count=int(open_count),
    )


def compare_latest_scans(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> dict | None:
    scans = [scan for scan in list_scans_for_asset(db, project_id=project_id, asset_id=asset_id) if scan.status == ScanStatus.COMPLETED]
    if len(scans) < 2:
        return None
    latest, previous = scans[0], scans[1]
    latest_findings = list_findings_for_scan(db, project_id=project_id, scan_id=latest.id)
    previous_findings = list_findings_for_scan(db, project_id=project_id, scan_id=previous.id)
    latest_codes = {item.finding_code or item.title for item in latest_findings}
    previous_codes = {item.finding_code or item.title for item in previous_findings}
    return {
        "latest_scan": ScanContextSnapshot(
            scan_id=str(latest.id),
            scan_date=(latest.completed_at or latest.created_at).isoformat()
            if (latest.completed_at or latest.created_at)
            else None,
            scan_type=latest.scan_type.value,
            status=latest.status.value,
            findings_count=len(latest_findings),
        ).model_dump(mode="json"),
        "previous_scan": ScanContextSnapshot(
            scan_id=str(previous.id),
            scan_date=(previous.completed_at or previous.created_at).isoformat()
            if (previous.completed_at or previous.created_at)
            else None,
            scan_type=previous.scan_type.value,
            status=previous.status.value,
            findings_count=len(previous_findings),
        ).model_dump(mode="json"),
        "new_findings": sorted(latest_codes - previous_codes),
        "resolved_findings": sorted(previous_codes - latest_codes),
        "unchanged_count": len(latest_codes & previous_codes),
    }
