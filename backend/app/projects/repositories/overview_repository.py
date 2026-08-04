import uuid

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.assets.models import Asset
from app.audit.models import AuditLog
from app.findings.enums import FindingStatus
from app.findings.models import Finding
from app.reports.models import Report
from app.scans.models import Scan


def count_project_assets(db: Session, *, project_id: uuid.UUID) -> int:
    return db.query(func.count(Asset.id)).filter(Asset.project_id == project_id).scalar() or 0


def count_project_scans(db: Session, *, project_id: uuid.UUID) -> int:
    return db.query(func.count(Scan.id)).filter(Scan.project_id == project_id).scalar() or 0


def count_project_findings(
    db: Session,
    *,
    project_id: uuid.UUID,
    status: FindingStatus | None = None,
) -> int:
    query = db.query(func.count(Finding.id)).filter(Finding.project_id == project_id)
    if status is not None:
        query = query.filter(Finding.status == status)
    return query.scalar() or 0


def count_project_reports(db: Session, *, project_id: uuid.UUID) -> int:
    return db.query(func.count(Report.id)).filter(Report.project_id == project_id).scalar() or 0


def list_project_recent_scans(
    db: Session,
    *,
    project_id: uuid.UUID,
    limit: int = 5,
) -> list[Scan]:
    return (
        db.query(Scan)
        .filter(Scan.project_id == project_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )


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


def _resource_ids_subquery(db: Session, model, project_id: uuid.UUID):
    return db.query(model.id).filter(model.project_id == project_id)


def list_project_activity(
    db: Session,
    *,
    organization_id: uuid.UUID,
    project_id: uuid.UUID,
    limit: int = 10,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    asset_ids = _resource_ids_subquery(db, Asset, project_id)
    scan_ids = _resource_ids_subquery(db, Scan, project_id)
    report_ids = _resource_ids_subquery(db, Report, project_id)
    finding_ids = _resource_ids_subquery(db, Finding, project_id)

    filters = or_(
        (AuditLog.resource_type == "project") & (AuditLog.resource_id == project_id),
        (AuditLog.resource_type == "asset") & AuditLog.resource_id.in_(asset_ids),
        (AuditLog.resource_type == "scan") & AuditLog.resource_id.in_(scan_ids),
        (AuditLog.resource_type == "report") & AuditLog.resource_id.in_(report_ids),
        (AuditLog.resource_type == "finding") & AuditLog.resource_id.in_(finding_ids),
    )

    base_query = db.query(AuditLog).filter(
        AuditLog.organization_id == organization_id,
        filters,
    )
    total = base_query.count()
    items = (
        base_query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    )
    return items, total
