import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.findings.enums import FindingStatus
from app.findings.models import Finding
from app.reports.models import Report
from app.risk.models import AssetRisk
from app.scans.models import Scan


def count_asset_scans(db: Session, *, project_id: uuid.UUID, asset_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Scan.id))
        .filter(Scan.project_id == project_id, Scan.asset_id == asset_id)
        .scalar()
        or 0
    )


def count_asset_findings(
    db: Session,
    *,
    asset_id: uuid.UUID,
    status: FindingStatus | None = None,
) -> int:
    query = db.query(func.count(Finding.id)).filter(Finding.asset_id == asset_id)
    if status is not None:
        query = query.filter(Finding.status == status)
    return query.scalar() or 0


def list_asset_recent_scans(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 5,
) -> list[Scan]:
    return (
        db.query(Scan)
        .filter(Scan.project_id == project_id, Scan.asset_id == asset_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )


def list_asset_open_findings(
    db: Session,
    *,
    asset_id: uuid.UUID,
    limit: int = 5,
) -> list[Finding]:
    return (
        db.query(Finding)
        .filter(Finding.asset_id == asset_id, Finding.status == FindingStatus.OPEN)
        .order_by(Finding.risk_score.desc(), Finding.created_at.desc())
        .limit(limit)
        .all()
    )


def list_asset_risk_trend(
    db: Session,
    *,
    asset_id: uuid.UUID,
    limit: int = 8,
) -> list[AssetRisk]:
    rows = (
        db.query(AssetRisk)
        .filter(AssetRisk.asset_id == asset_id)
        .order_by(AssetRisk.calculated_at.desc())
        .limit(limit)
        .all()
    )
    return list(reversed(rows))


def list_project_recent_reports(
    db: Session,
    *,
    project_id: uuid.UUID,
    limit: int = 5,
) -> list[Report]:
    return (
        db.query(Report)
        .filter(Report.project_id == project_id)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .all()
    )


def list_asset_activity(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    limit: int = 10,
) -> list[AuditLog]:
    scan_ids = db.query(Scan.id).filter(
        Scan.project_id == project_id,
        Scan.asset_id == asset_id,
    )
    finding_ids = db.query(Finding.id).filter(Finding.asset_id == asset_id)

    filters = or_(
        (AuditLog.resource_type == "asset") & (AuditLog.resource_id == asset_id),
        (AuditLog.resource_type == "scan") & AuditLog.resource_id.in_(scan_ids),
        (AuditLog.resource_type == "finding") & AuditLog.resource_id.in_(finding_ids),
    )

    return (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == organization_id, filters)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )
