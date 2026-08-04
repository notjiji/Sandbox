import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.risk.models import (
    AssetRisk,
    OrganizationRisk,
    OrganizationRiskHistory,
    ProjectRiskMetric,
    Recommendation,
    RiskRule,
)


def get_rule_for_finding(
    db: Session,
    *,
    plugin: str,
    finding_code: str,
) -> RiskRule | None:
    return (
        db.query(RiskRule)
        .filter(
            RiskRule.plugin == plugin,
            RiskRule.finding_code == finding_code,
            RiskRule.enabled.is_(True),
        )
        .first()
    )


def get_recommendation_by_code(db: Session, *, code: str) -> Recommendation | None:
    return db.query(Recommendation).filter(Recommendation.code == code).first()


def save_project_risk_metric(
    db: Session,
    *,
    project_id: uuid.UUID,
    total_risk: float,
    security_score: float,
    grade: str,
    risk_level: str,
    open_findings: int,
    breakdown: dict,
    top_issues: list[dict],
) -> ProjectRiskMetric:
    metric = ProjectRiskMetric(
        project_id=project_id,
        total_risk=total_risk,
        security_score=security_score,
        grade=grade,
        risk_level=risk_level,
        open_findings=open_findings,
        breakdown=breakdown,
        top_issues=top_issues,
        calculated_at=datetime.now(UTC),
    )
    db.add(metric)
    db.flush()
    return metric


def get_latest_project_risk_metric(
    db: Session,
    *,
    project_id: uuid.UUID,
) -> ProjectRiskMetric | None:
    return (
        db.query(ProjectRiskMetric)
        .filter(ProjectRiskMetric.project_id == project_id)
        .order_by(ProjectRiskMetric.calculated_at.desc())
        .first()
    )


def save_asset_risk(
    db: Session,
    *,
    asset_id: uuid.UUID,
    scan_id: uuid.UUID | None,
    total_risk: float,
    score: float,
    grade: str,
    breakdown: dict[str, int],
) -> AssetRisk:
    record = AssetRisk(
        asset_id=asset_id,
        scan_id=scan_id,
        total_risk=total_risk,
        score=score,
        grade=grade,
        critical_count=breakdown.get("critical", 0),
        high_count=breakdown.get("high", 0),
        medium_count=breakdown.get("medium", 0),
        low_count=breakdown.get("low", 0),
        calculated_at=datetime.now(UTC),
    )
    db.add(record)
    db.flush()
    return record


def list_assets_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> list:
    from app.assets.models import Asset

    return (
        db.query(Asset)
        .filter(
            Asset.organization_id == organization_id,
            Asset.deleted_at.is_(None),
        )
        .order_by(Asset.name.asc())
        .all()
    )


def get_latest_asset_risk_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
    asset_id: uuid.UUID,
) -> AssetRisk | None:
    from app.assets.models import Asset

    return (
        db.query(AssetRisk)
        .join(Asset, Asset.id == AssetRisk.asset_id)
        .filter(
            AssetRisk.asset_id == asset_id,
            Asset.organization_id == organization_id,
            Asset.deleted_at.is_(None),
        )
        .order_by(AssetRisk.calculated_at.desc())
        .first()
    )


def get_latest_asset_risk(db: Session, *, asset_id: uuid.UUID) -> AssetRisk | None:
    """Internal use only — prefer get_latest_asset_risk_for_organization."""
    return (
        db.query(AssetRisk)
        .filter(AssetRisk.asset_id == asset_id)
        .order_by(AssetRisk.calculated_at.desc())
        .first()
    )


def get_latest_asset_risks_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> list[AssetRisk]:
    from app.assets.models import Asset

    subq = (
        db.query(AssetRisk.asset_id, AssetRisk.calculated_at)
        .join(Asset, Asset.id == AssetRisk.asset_id)
        .filter(Asset.organization_id == organization_id)
        .distinct(AssetRisk.asset_id)
        .order_by(AssetRisk.asset_id, AssetRisk.calculated_at.desc())
    )
    # Simpler approach: get all asset risks, pick latest per asset in Python
    rows = (
        db.query(AssetRisk)
        .join(Asset, Asset.id == AssetRisk.asset_id)
        .filter(Asset.organization_id == organization_id)
        .order_by(AssetRisk.calculated_at.desc())
        .all()
    )
    latest: dict[uuid.UUID, AssetRisk] = {}
    for row in rows:
        if row.asset_id not in latest:
            latest[row.asset_id] = row
    return list(latest.values())


def upsert_organization_risk(
    db: Session,
    *,
    organization_id: uuid.UUID,
    overall_score: float,
    total_risk: float,
    grade: str,
    risk_level: str,
    trend: str,
) -> OrganizationRisk:
    record = (
        db.query(OrganizationRisk)
        .filter(OrganizationRisk.organization_id == organization_id)
        .first()
    )
    if record is None:
        record = OrganizationRisk(organization_id=organization_id)
        db.add(record)
    record.overall_score = overall_score
    record.total_risk = total_risk
    record.grade = grade
    record.risk_level = risk_level
    record.trend = trend
    db.flush()
    return record


def get_organization_risk(db: Session, *, organization_id: uuid.UUID) -> OrganizationRisk | None:
    return (
        db.query(OrganizationRisk)
        .filter(OrganizationRisk.organization_id == organization_id)
        .first()
    )


def save_organization_risk_history(
    db: Session,
    *,
    organization_id: uuid.UUID,
    overall_score: float,
    total_risk: float,
    grade: str,
) -> OrganizationRiskHistory:
    entry = OrganizationRiskHistory(
        organization_id=organization_id,
        overall_score=overall_score,
        total_risk=total_risk,
        grade=grade,
        calculated_at=datetime.now(UTC),
    )
    db.add(entry)
    db.flush()
    return entry


def list_organization_risk_history(
    db: Session,
    *,
    organization_id: uuid.UUID,
    limit: int = 30,
) -> list[OrganizationRiskHistory]:
    return (
        db.query(OrganizationRiskHistory)
        .filter(OrganizationRiskHistory.organization_id == organization_id)
        .order_by(OrganizationRiskHistory.calculated_at.asc())
        .limit(limit)
        .all()
    )


def get_previous_organization_score(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> float | None:
    rows = (
        db.query(OrganizationRiskHistory)
        .filter(OrganizationRiskHistory.organization_id == organization_id)
        .order_by(OrganizationRiskHistory.calculated_at.desc())
        .limit(2)
        .all()
    )
    if len(rows) < 2:
        return None
    return float(rows[1].overall_score)
