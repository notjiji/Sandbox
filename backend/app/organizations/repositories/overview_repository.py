import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.assets.models import Asset
from app.audit.models import AuditLog
from app.audit.repositories.audit_repository import search_audit_logs
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.members.enums import MemberStatus
from app.members.models import OrganizationMember
from app.projects.models import Project
from app.reports.models import Report
from app.risk.models import OrganizationRiskHistory
from app.scans.models import Scan

ANALYTICS_PERIOD_DAYS = 30


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
        .filter(
            Asset.organization_id == organization_id,
            Asset.deleted_at.is_(None),
        )
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


def _period_start(days: int = ANALYTICS_PERIOD_DAYS) -> datetime:
    return datetime.now(UTC) - timedelta(days=days)


def count_assets_since(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> int:
    return (
        db.query(func.count(Asset.id))
        .filter(
            Asset.organization_id == organization_id,
            Asset.created_at >= since,
            Asset.deleted_at.is_(None),
        )
        .scalar()
        or 0
    )


def count_projects_since(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> int:
    return (
        db.query(func.count(Project.id))
        .filter(
            Project.organization_id == organization_id,
            Project.created_at >= since,
        )
        .scalar()
        or 0
    )


def count_members_since(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> int:
    return (
        db.query(func.count(OrganizationMember.id))
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.status == MemberStatus.ACTIVE,
            or_(
                OrganizationMember.joined_at >= since,
                OrganizationMember.created_at >= since,
            ),
        )
        .scalar()
        or 0
    )


def count_scans_since(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> int:
    return (
        db.query(func.count(Scan.id))
        .join(Project, Scan.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Scan.created_at >= since,
        )
        .scalar()
        or 0
    )


def count_reports_since(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> int:
    return (
        db.query(func.count(Report.id))
        .join(Project, Report.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Report.created_at >= since,
        )
        .scalar()
        or 0
    )


def count_critical_findings_change(
    db: Session,
    *,
    organization_id: uuid.UUID,
    since: datetime,
) -> int:
    org_filter = (
        db.query(Finding.id)
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.severity == FindingSeverity.CRITICAL,
        )
    )
    new_critical = (
        org_filter.filter(Finding.created_at >= since).count()
    )
    resolved_critical = (
        db.query(func.count(Finding.id))
        .join(Project, Finding.project_id == Project.id)
        .filter(
            Project.organization_id == organization_id,
            Finding.severity == FindingSeverity.CRITICAL,
            Finding.created_at < since,
            Finding.status.in_(
                [
                    FindingStatus.RESOLVED,
                    FindingStatus.FALSE_POSITIVE,
                    FindingStatus.ACCEPTED,
                ]
            ),
            Finding.updated_at >= since,
        )
        .scalar()
        or 0
    )
    return int(new_critical - resolved_critical)


def get_risk_score_at_or_before(
    db: Session,
    *,
    organization_id: uuid.UUID,
    at: datetime,
) -> float | None:
    row = (
        db.query(OrganizationRiskHistory)
        .filter(
            OrganizationRiskHistory.organization_id == organization_id,
            OrganizationRiskHistory.calculated_at <= at,
        )
        .order_by(OrganizationRiskHistory.calculated_at.desc())
        .first()
    )
    if row is None:
        return None
    return float(row.overall_score)


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
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    actor: str | None = None,
    asset_id: uuid.UUID | None = None,
    severity: str | None = None,
    date_from=None,
    date_to=None,
) -> tuple[list[AuditLog], int]:
    return search_audit_logs(
        db,
        organization_id=organization_id,
        action=action,
        user_id=user_id,
        actor=actor,
        asset_id=asset_id,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        exclude_prefixes=("auth.", "user."),
        limit=limit,
        offset=offset,
    )
