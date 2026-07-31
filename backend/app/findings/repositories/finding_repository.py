import uuid

from sqlalchemy.orm import Session, joinedload

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding


def create_finding(
    db: Session,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    asset_id: uuid.UUID,
    title: str,
    description: str | None = None,
    severity: FindingSeverity = FindingSeverity.MEDIUM,
    status: FindingStatus = FindingStatus.OPEN,
) -> Finding:
    finding = Finding(
        project_id=project_id,
        scan_id=scan_id,
        asset_id=asset_id,
        title=title,
        description=description,
        severity=severity,
        status=status,
    )
    db.add(finding)
    db.flush()
    return finding


def list_findings_for_project(db: Session, *, project_id: uuid.UUID) -> list[Finding]:
    return (
        db.query(Finding)
        .options(joinedload(Finding.asset))
        .filter(Finding.project_id == project_id)
        .order_by(Finding.created_at.desc())
        .all()
    )


def get_finding_by_id(
    db: Session,
    *,
    project_id: uuid.UUID,
    finding_id: uuid.UUID,
) -> Finding | None:
    return (
        db.query(Finding)
        .filter(Finding.id == finding_id, Finding.project_id == project_id)
        .first()
    )


def update_finding(
    db: Session,
    finding: Finding,
    *,
    title: str | None = None,
    description: str | None = None,
    severity: FindingSeverity | None = None,
    status: FindingStatus | None = None,
) -> Finding:
    if title is not None:
        finding.title = title
    if description is not None:
        finding.description = description
    if severity is not None:
        finding.severity = severity
    if status is not None:
        finding.status = status
    db.add(finding)
    db.flush()
    return finding
