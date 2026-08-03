import uuid

from sqlalchemy.orm import Session

from app.findings.enums import FindingSeverity
from app.risk.models import ProjectRiskMetric, RiskRule


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


def list_enabled_rules(db: Session) -> list[RiskRule]:
    return (
        db.query(RiskRule)
        .filter(RiskRule.enabled.is_(True))
        .order_by(RiskRule.plugin, RiskRule.finding_code)
        .all()
    )


def save_project_risk_metric(
    db: Session,
    *,
    project_id: uuid.UUID,
    score: float,
    open_findings: int,
    breakdown: dict,
    top_issues: list[dict],
) -> ProjectRiskMetric:
    from datetime import UTC, datetime

    metric = ProjectRiskMetric(
        project_id=project_id,
        score=score,
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
