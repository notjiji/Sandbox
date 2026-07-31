import uuid

from sqlalchemy.orm import Session

from app.models.finding import Finding, FindingSeverity, FindingStatus


def list_findings_for_project(db: Session, *, project_id: uuid.UUID) -> list[Finding]:
    return (
        db.query(Finding)
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
