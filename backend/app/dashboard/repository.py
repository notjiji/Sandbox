"""Dashboard aggregation queries."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.assets.enums import AssetType
from app.assets.models import Asset
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.repositories.finding_repository import SEVERITY_ORDER
from app.projects.models import Project
from app.risk.models import AssetRisk
from app.risk.schemas import SeverityBreakdown
from app.scans.models import Scan, ScanPluginRun
from app.scans.schedule_models import AssetScanSchedule
from app.scans.services.scan_service import _compute_duration_seconds

WEBSITE_TYPES = frozenset({AssetType.WEBSITE, AssetType.API_ENDPOINT})
DOMAIN_TYPES = frozenset({AssetType.DOMAIN, AssetType.EMAIL_DOMAIN})
IP_TYPES = frozenset({AssetType.PUBLIC_IP})
SERVER_TYPES = frozenset(
    {AssetType.SERVER, AssetType.WINDOWS_SERVER, AssetType.DOCKER_HOST}
)


def get_primary_project_id(db: Session, *, organization_id: uuid.UUID) -> uuid.UUID | None:
    row = (
        db.query(Project.id)
        .filter(Project.organization_id == organization_id, Project.is_active.is_(True))
        .order_by(Project.created_at.asc())
        .first()
    )
    return row[0] if row else None


def count_assets_by_category(db: Session, *, organization_id: uuid.UUID) -> dict[str, int]:
    rows = (
        db.query(Asset.type, func.count(Asset.id))
        .filter(
            Asset.organization_id == organization_id,
            Asset.deleted_at.is_(None),
        )
        .group_by(Asset.type)
        .all()
    )
    counts = {"websites": 0, "domains": 0, "ips": 0, "servers": 0, "total": 0}
    for asset_type, count in rows:
        counts["total"] += int(count)
        if asset_type in WEBSITE_TYPES:
            counts["websites"] += int(count)
        elif asset_type in DOMAIN_TYPES:
            counts["domains"] += int(count)
        elif asset_type in IP_TYPES:
            counts["ips"] += int(count)
        elif asset_type in SERVER_TYPES:
            counts["servers"] += int(count)
    return counts


def count_open_findings_by_severity(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> SeverityBreakdown:
    rows = (
        db.query(Finding.severity, func.count(Finding.id))
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.status == FindingStatus.OPEN,
        )
        .group_by(Finding.severity)
        .all()
    )
    breakdown = SeverityBreakdown()
    for severity, count in rows:
        key = severity.value if hasattr(severity, "value") else str(severity)
        if key == "critical":
            breakdown.critical = int(count)
        elif key == "high":
            breakdown.high = int(count)
        elif key == "medium":
            breakdown.medium = int(count)
        elif key == "low":
            breakdown.low = int(count)
        elif key == "info":
            breakdown.info = int(count)
    return breakdown


def list_top_open_findings(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int = 5,
) -> list[Finding]:
    return (
        db.query(Finding)
        .options(joinedload(Finding.asset))
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.status == FindingStatus.OPEN,
            Finding.severity.in_([FindingSeverity.CRITICAL, FindingSeverity.HIGH]),
        )
        .order_by(SEVERITY_ORDER.desc(), Finding.risk_score.desc(), Finding.created_at.desc())
        .limit(limit)
        .all()
    )


def get_latest_scan(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> Scan | None:
    return (
        db.query(Scan)
        .options(joinedload(Scan.asset))
        .join(Project, Scan.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .order_by(Scan.created_at.desc())
        .first()
    )


def list_upcoming_schedules_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
    after: datetime | None = None,
    limit: int = 10,
) -> list[AssetScanSchedule]:
    now = after or datetime.now(UTC)
    return (
        db.query(AssetScanSchedule)
        .options(joinedload(AssetScanSchedule.asset))
        .join(Asset, AssetScanSchedule.asset_id == Asset.id)
        .filter(
            Asset.organization_id == organization_id,
            Asset.deleted_at.is_(None),
            AssetScanSchedule.enabled.is_(True),
            AssetScanSchedule.next_run_at.isnot(None),
            AssetScanSchedule.next_run_at >= now,
        )
        .order_by(AssetScanSchedule.next_run_at.asc())
        .limit(limit)
        .all()
    )


def list_scan_history_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
    limit: int = 100,
) -> list[dict]:
    findings_subq = (
        db.query(Finding.scan_id.label("scan_id"), func.count(Finding.id).label("findings"))
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.scan_id.isnot(None),
        )
        .group_by(Finding.scan_id)
        .subquery()
    )
    plugins_subq = (
        db.query(
            ScanPluginRun.scan_id.label("scan_id"),
            func.count(ScanPluginRun.id).label("plugins"),
        )
        .group_by(ScanPluginRun.scan_id)
        .subquery()
    )
    risk_subq = (
        db.query(AssetRisk.scan_id.label("scan_id"), AssetRisk.score.label("score"))
        .filter(AssetRisk.scan_id.isnot(None))
        .subquery()
    )

    rows = (
        db.query(
            Scan,
            Asset.name.label("asset_name"),
            func.coalesce(findings_subq.c.findings, 0).label("findings"),
            func.coalesce(plugins_subq.c.plugins, 0).label("plugins"),
            risk_subq.c.score.label("score"),
        )
        .join(Project, Scan.project_id == Project.id)
        .join(Asset, Scan.asset_id == Asset.id)
        .outerjoin(findings_subq, findings_subq.c.scan_id == Scan.id)
        .outerjoin(plugins_subq, plugins_subq.c.scan_id == Scan.id)
        .outerjoin(risk_subq, risk_subq.c.scan_id == Scan.id)
        .filter(
            Project.organization_id == organization_id,
            Scan.created_at >= since,
        )
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )

    output: list[dict] = []
    for scan, asset_name, findings, plugins, score in rows:
        output.append(
            {
                "scan_id": str(scan.id),
                "date": scan.completed_at or scan.failed_at or scan.cancelled_at or scan.created_at,
                "asset_id": str(scan.asset_id),
                "asset_name": asset_name or "Unknown asset",
                "project_id": str(scan.project_id),
                "duration_seconds": _compute_duration_seconds(scan),
                "plugins": int(plugins or 0),
                "findings": int(findings or 0),
                "score": float(score) if score is not None else None,
                "status": scan.status.value if hasattr(scan.status, "value") else str(scan.status),
            }
        )
    return output


def list_finding_trend_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> list[dict]:
    day_expr = func.date(Finding.created_at)
    rows = (
        db.query(
            day_expr.label("day"),
            Finding.severity.label("severity"),
            func.count(Finding.id).label("count"),
        )
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.status == FindingStatus.OPEN,
            Finding.created_at >= since,
        )
        .group_by(day_expr, Finding.severity)
        .order_by(day_expr)
        .all()
    )

    by_day: dict[datetime, dict[str, int]] = {}
    for day, severity, count in rows:
        if isinstance(day, str):
            parsed_day = datetime.fromisoformat(day).replace(tzinfo=UTC)
        else:
            parsed_day = day
        if parsed_day not in by_day:
            by_day[parsed_day] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        key = severity.value if hasattr(severity, "value") else str(severity)
        if key in by_day[parsed_day]:
            by_day[parsed_day][key] = int(count)

    output: list[dict] = []
    for day, counts in by_day.items():
        output.append(
            {
                "date": day,
                "critical": counts["critical"],
                "high": counts["high"],
                "medium": counts["medium"],
                "low": counts["low"],
            }
        )
    return output
