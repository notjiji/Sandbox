import uuid

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.assets.models import Asset
from app.audit.models import AuditLog
from app.findings.enums import FindingStatus
from app.findings.models import Finding
from app.members.models import OrganizationMember
from app.projects.models import Project
from app.reports.models import Report
from app.scans.models import Scan


def count_projects(db: Session, *, organization_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Project.id))
        .filter(Project.organization_id == organization_id, Project.is_active.is_(True))
        .scalar()
        or 0
    )


def count_assets(db: Session, *, organization_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Asset.id))
        .filter(Asset.organization_id == organization_id)
        .scalar()
        or 0
    )


def count_members(db: Session, *, organization_id: uuid.UUID) -> int:
    return (
        db.query(func.count(OrganizationMember.id))
        .filter(OrganizationMember.organization_id == organization_id)
        .scalar()
        or 0
    )


def count_scans(db: Session, *, organization_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Scan.id))
        .join(Project, Scan.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .scalar()
        or 0
    )


def count_findings(
    db: Session,
    *,
    organization_id: uuid.UUID,
    status: FindingStatus | None = None,
) -> int:
    query = (
        db.query(func.count(Finding.id))
        .join(Project, Finding.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
    )
    if status is not None:
        query = query.filter(Finding.status == status)
    return query.scalar() or 0


def count_reports(db: Session, *, organization_id: uuid.UUID) -> int:
    return (
        db.query(func.count(Report.id))
        .join(Project, Report.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .scalar()
        or 0
    )


def list_recent_scans(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int = 5,
) -> list[Scan]:
    return (
        db.query(Scan)
        .join(Project, Scan.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .order_by(Scan.created_at.desc())
        .limit(limit)
        .all()
    )


def list_recent_reports(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int = 5,
) -> list[Report]:
    return (
        db.query(Report)
        .join(Project, Report.project_id == Project.id)
        .filter(Project.organization_id == organization_id)
        .order_by(Report.created_at.desc())
        .limit(limit)
        .all()
    )


def list_recent_activity(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int = 10,
) -> list[AuditLog]:
    return list_organization_activity(
        db,
        organization_id=organization_id,
        limit=limit,
        offset=0,
    )[0]


def list_organization_activity(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    base_query = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)
    for prefix in ("auth.", "user."):
        base_query = base_query.filter(~AuditLog.action.startswith(prefix))

    total = base_query.count()
    items = (
        base_query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    )
    return items, total
