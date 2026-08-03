import uuid
from datetime import datetime

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
    plugin: str | None = None,
    finding_code: str | None = None,
    check_status: str | None = None,
    risk_score: float = 0.0,
    description: str | None = None,
    severity: FindingSeverity = FindingSeverity.MEDIUM,
    status: FindingStatus = FindingStatus.OPEN,
    evidence: str | None = None,
    recommendation: str | None = None,
    references: list[str] | None = None,
    raw_data: dict | None = None,
    confidence: float | None = None,
    detected_at: datetime | None = None,
) -> Finding:
    finding = Finding(
        project_id=project_id,
        scan_id=scan_id,
        asset_id=asset_id,
        plugin=plugin,
        finding_code=finding_code,
        check_status=check_status,
        title=title,
        description=description,
        severity=severity,
        risk_score=risk_score,
        status=status,
        evidence=evidence,
        recommendation=recommendation,
        references=references,
        raw_data=raw_data,
        confidence=confidence,
        detected_at=detected_at,
    )
    db.add(finding)
    db.flush()
    return finding


def list_findings_for_project(db: Session, *, project_id: uuid.UUID) -> list[Finding]:
    return (
        db.query(Finding)
        .options(joinedload(Finding.asset))
        .filter(Finding.project_id == project_id)
        .order_by(Finding.risk_score.desc(), Finding.created_at.desc())
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
    risk_score: float | None = None,
) -> Finding:
    if title is not None:
        finding.title = title
    if description is not None:
        finding.description = description
    if severity is not None:
        finding.severity = severity
    if status is not None:
        finding.status = status
    if risk_score is not None:
        finding.risk_score = risk_score
    db.add(finding)
    db.flush()
    return finding
