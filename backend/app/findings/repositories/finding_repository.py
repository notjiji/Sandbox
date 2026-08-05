import uuid
from datetime import UTC, datetime

from sqlalchemy import String, case, cast, func, or_
from sqlalchemy.orm import Session, joinedload

from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.schemas import FindingListQuery

SEVERITY_ORDER = case(
    (Finding.severity == FindingSeverity.CRITICAL, 5),
    (Finding.severity == FindingSeverity.HIGH, 4),
    (Finding.severity == FindingSeverity.MEDIUM, 3),
    (Finding.severity == FindingSeverity.LOW, 2),
    else_=1,
)


def list_findings_for_scan(
    db: Session,
    *,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
) -> list[Finding]:
    return (
        db.query(Finding)
        .filter(Finding.project_id == project_id, Finding.scan_id == scan_id)
        .order_by(Finding.risk_score.desc(), Finding.created_at.desc())
        .all()
    )


def count_findings_for_scans(
    db: Session,
    *,
    scan_ids: list[uuid.UUID],
) -> dict[uuid.UUID, int]:
    if not scan_ids:
        return {}

    rows = (
        db.query(Finding.scan_id, func.count(Finding.id))
        .filter(Finding.scan_id.in_(scan_ids))
        .group_by(Finding.scan_id)
        .all()
    )
    return {scan_id: int(count) for scan_id, count in rows if scan_id is not None}


def list_finding_changes_between(
    db: Session,
    *,
    asset_id: uuid.UUID,
    since: datetime,
    until: datetime,
) -> tuple[list[Finding], list[Finding]]:
    new_findings = (
        db.query(Finding)
        .filter(
            Finding.asset_id == asset_id,
            Finding.created_at > since,
            Finding.created_at <= until,
        )
        .order_by(Finding.risk_score.desc())
        .all()
    )
    resolved_findings = (
        db.query(Finding)
        .filter(
            Finding.asset_id == asset_id,
            Finding.status == FindingStatus.RESOLVED,
            Finding.updated_at > since,
            Finding.updated_at <= until,
        )
        .order_by(Finding.risk_score.desc())
        .all()
    )
    return new_findings, resolved_findings


def list_findings_for_asset_paginated(
    db: Session,
    *,
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    query: FindingListQuery,
) -> tuple[list[Finding], int]:
    base = db.query(Finding).filter(
        Finding.project_id == project_id,
        Finding.asset_id == asset_id,
    )

    if query.status_group == "open":
        base = base.filter(
            Finding.status.in_((FindingStatus.OPEN, FindingStatus.IN_REVIEW))
        )
    elif query.status_group == "resolved":
        base = base.filter(Finding.status == FindingStatus.RESOLVED)
    elif query.status_group == "ignored":
        base = base.filter(
            Finding.status.in_((FindingStatus.FALSE_POSITIVE, FindingStatus.ACCEPTED))
        )
    elif query.status is not None:
        base = base.filter(Finding.status == query.status)

    if query.severity is not None:
        base = base.filter(Finding.severity == query.severity)

    if query.search:
        needle = f"%{query.search.strip().lower()}%"
        base = base.filter(
            or_(
                func.lower(Finding.title).like(needle),
                func.lower(Finding.description).like(needle),
                func.lower(Finding.finding_code).like(needle),
                cast(Finding.status, String).ilike(needle),
            )
        )

    total = base.count()

    sort_key = query.sort
    if sort_key == "severity":
        sort_column = SEVERITY_ORDER
    elif sort_key == "title":
        sort_column = Finding.title
    elif sort_key == "created_at":
        sort_column = Finding.created_at
    else:
        sort_column = Finding.risk_score

    if query.order == "asc":
        base = base.order_by(sort_column.asc(), Finding.created_at.desc())
    else:
        base = base.order_by(sort_column.desc(), Finding.created_at.desc())

    offset = (query.page - 1) * query.limit
    items = base.offset(offset).limit(query.limit).all()
    return items, int(total)


def list_findings_for_asset_all(db: Session, *, asset_id: uuid.UUID) -> list[Finding]:
    return (
        db.query(Finding)
        .options(joinedload(Finding.asset))
        .filter(Finding.asset_id == asset_id)
        .order_by(Finding.risk_score.desc(), Finding.created_at.desc())
        .all()
    )


list_findings_for_asset = list_findings_for_asset_all


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
    recommendation_id: str | None = None,
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
        recommendation_id=recommendation_id,
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
