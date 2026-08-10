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
from app.risk.schemas import SeverityBreakdown
from app.scans.models import Scan
from app.scans.schedule_models import AssetScanSchedule

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
