"""Risk Engine — reads findings, applies rules, scores, prioritizes, stores metrics.

The Risk Engine never performs scans. Scanners report finding codes; rules assign severity and score.
"""

from dataclasses import dataclass
from datetime import UTC, datetime
import uuid

from sqlalchemy.orm import Session

from app.assets.enums import CRITICALITY_RISK_MULTIPLIERS, AssetCriticality
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.repositories.finding_repository import list_findings_for_project
from app.plugins.output import PluginFinding, PluginFindingStatus
from app.risk.models import ProjectRiskMetric, RiskRule
from app.risk.repositories.risk_repository import (
    get_rule_for_finding,
    get_latest_project_risk_metric,
    save_project_risk_metric,
)
from app.risk.schemas import PrioritizedFinding, ProjectRiskResponse, SeverityBreakdown


@dataclass(frozen=True)
class ResolvedFinding:
    finding_code: str
    title: str
    description: str | None
    severity: FindingSeverity
    risk_score: float
    evidence: str | None
    raw_data: dict
    check_status: str
    detected_at: datetime | None


class RiskEngine:
    """Applies risk rules to normalized plugin findings and calculates project risk."""

    def resolve_finding(self, db: Session, *, plugin_finding: PluginFinding) -> ResolvedFinding | None:
        """Map a plugin-reported finding to rule-derived severity and score."""
        if plugin_finding.status == PluginFindingStatus.PASSED:
            return None

        rule = get_rule_for_finding(
            db,
            plugin=plugin_finding.plugin,
            finding_code=plugin_finding.code,
        )
        if rule:
            return ResolvedFinding(
                finding_code=rule.finding_code,
                title=rule.title,
                description=rule.description,
                severity=rule.severity,
                risk_score=float(rule.score),
                evidence=plugin_finding.evidence,
                raw_data=plugin_finding.raw_data,
                check_status=plugin_finding.status.value,
                detected_at=plugin_finding.detected_at,
            )

        return ResolvedFinding(
            finding_code=plugin_finding.code,
            title=plugin_finding.code.replace("_", " ").title(),
            description="No matching risk rule configured.",
            severity=FindingSeverity.MEDIUM,
            risk_score=0.0,
            evidence=plugin_finding.evidence,
            raw_data=plugin_finding.raw_data,
            check_status=plugin_finding.status.value,
            detected_at=plugin_finding.detected_at,
        )

    def score_open_findings(self, findings: list[Finding]) -> float:
        total = 0.0
        for finding in findings:
            if finding.status != FindingStatus.OPEN:
                continue
            multiplier = 1.0
            if finding.asset and finding.asset.criticality:
                try:
                    multiplier = CRITICALITY_RISK_MULTIPLIERS[
                        AssetCriticality(finding.asset.criticality.value)
                    ]
                except ValueError:
                    multiplier = 1.0
            total += float(finding.risk_score or 0.0) * multiplier
        return total

    def build_breakdown(self, findings: list[Finding]) -> SeverityBreakdown:
        breakdown = SeverityBreakdown()
        for finding in findings:
            if finding.status != FindingStatus.OPEN:
                continue
            severity = finding.severity.value
            setattr(breakdown, severity, getattr(breakdown, severity) + 1)
        return breakdown

    def prioritize_findings(self, findings: list[Finding], *, limit: int = 10) -> list[PrioritizedFinding]:
        open_findings = [f for f in findings if f.status == FindingStatus.OPEN]
        ranked = sorted(
            open_findings,
            key=lambda finding: (
                float(finding.risk_score or 0.0),
                finding.severity.value,
            ),
            reverse=True,
        )
        prioritized: list[PrioritizedFinding] = []
        for finding in ranked[:limit]:
            multiplier = 1.0
            if finding.asset and finding.asset.criticality:
                try:
                    multiplier = CRITICALITY_RISK_MULTIPLIERS[
                        AssetCriticality(finding.asset.criticality.value)
                    ]
                except ValueError:
                    multiplier = 1.0
            prioritized.append(
                PrioritizedFinding(
                    finding_id=str(finding.id),
                    finding_code=finding.finding_code or "",
                    title=finding.title,
                    severity=finding.severity,
                    risk_score=float(finding.risk_score or 0.0),
                    weighted_score=float(finding.risk_score or 0.0) * multiplier,
                    asset_id=str(finding.asset_id),
                )
            )
        return prioritized

    def calculate_project_risk(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        store: bool = True,
    ) -> ProjectRiskResponse:
        findings = list_findings_for_project(db, project_id=project_id)
        open_findings = [f for f in findings if f.status == FindingStatus.OPEN]
        score = self.score_open_findings(open_findings)
        breakdown = self.build_breakdown(open_findings)
        top_issues = self.prioritize_findings(open_findings)

        if store:
            save_project_risk_metric(
                db,
                project_id=project_id,
                score=score,
                open_findings=len(open_findings),
                breakdown=breakdown.model_dump(),
                top_issues=[issue.model_dump(mode="json") for issue in top_issues],
            )

        return ProjectRiskResponse(
            project_id=str(project_id),
            score=score,
            open_findings=len(open_findings),
            breakdown=breakdown,
            top_issues=top_issues,
            calculated_at=datetime.now(UTC),
        )

    def get_or_calculate_project_risk(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
    ) -> ProjectRiskResponse:
        latest = get_latest_project_risk_metric(db, project_id=project_id)
        if latest:
            return ProjectRiskResponse(
                project_id=str(project_id),
                score=float(latest.score),
                open_findings=latest.open_findings,
                breakdown=SeverityBreakdown.model_validate(latest.breakdown or {}),
                top_issues=[
                    PrioritizedFinding.model_validate(item) for item in (latest.top_issues or [])
                ],
                calculated_at=latest.calculated_at,
            )
        return self.calculate_project_risk(db, project_id=project_id, store=True)


risk_engine = RiskEngine()
