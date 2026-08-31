"""Risk Engine — reads findings, applies rules, scores, prioritizes, stores metrics."""

from dataclasses import dataclass
from datetime import UTC, datetime
import uuid
from collections import Counter

from sqlalchemy.orm import Session

from app.audit.events import AuditAction
from app.audit.service import record_audit_event
from app.assets.enums import AssetCriticality
from app.assets.models import Asset
from app.findings.enums import FindingSeverity, FindingStatus
from app.findings.models import Finding
from app.findings.repositories.finding_repository import (
    list_findings_for_asset,
    list_findings_for_project,
)
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding
from app.core.risk_engine.scoring import (
    SEVERITY_SORT_ORDER,
    compute_trend,
    grade_from_security_score,
    points_for_severity,
    risk_level_from_security_score,
    security_score,
    total_risk,
)
from app.risk.repositories.risk_repository import (
    get_latest_asset_risk,
    get_latest_asset_risks_for_organization,
    get_latest_project_risk_metric,
    get_organization_risk,
    get_previous_organization_score,
    get_recommendation_by_code,
    get_rule_for_finding,
    list_assets_for_organization,
    list_organization_risk_history,
    save_asset_risk,
    save_organization_risk_history,
    save_project_risk_metric,
    upsert_organization_risk,
)
from app.risk.schemas import (
    AssetRiskResponse,
    DashboardMetrics,
    OrganizationRiskResponse,
    PrioritizedFinding,
    ProjectRiskResponse,
    RiskTrendPoint,
    SeverityBreakdown,
    unscanned_asset_risk,
)


@dataclass(frozen=True)
class ResolvedFinding:
    finding_code: str
    title: str
    description: str | None
    severity: FindingSeverity
    risk_score: float
    recommendation_id: str | None
    recommendation_text: str | None
    evidence: str | None
    raw_data: dict
    check_status: str
    detected_at: datetime | None
    category: str | None = None
    references: list[str] | None = None
    confidence: float | None = None
    cvss: float | None = None
    cwe: str | None = None
    cve: str | None = None


class RiskEngine:
    @staticmethod
    def _asset_risk_from_record(record) -> AssetRiskResponse:
        return AssetRiskResponse(
            asset_id=str(record.asset_id),
            scanned=True,
            scan_id=str(record.scan_id) if record.scan_id else None,
            total_risk=float(record.total_risk),
            score=float(record.score),
            grade=record.grade,
            critical_count=record.critical_count,
            high_count=record.high_count,
            medium_count=record.medium_count,
            low_count=record.low_count,
            calculated_at=record.calculated_at,
        )

    def resolve_finding(self, db: Session, *, plugin_finding: ScanFinding) -> ResolvedFinding | None:
        if plugin_finding.status == FindingCheckStatus.PASSED:
            return None

        rule_id = plugin_finding.rule_id
        rule = get_rule_for_finding(
            db,
            plugin=plugin_finding.plugin,
            finding_code=rule_id,
        )
        if rule:
            severity = rule.severity
            score = float(rule.score) if rule.score is not None else points_for_severity(severity)
            recommendation_id = rule.recommendation_id
            rec = (
                get_recommendation_by_code(db, code=recommendation_id)
                if recommendation_id
                else None
            )
            return ResolvedFinding(
                finding_code=rule.finding_code,
                title=rule.title,
                description=rule.description or plugin_finding.description,
                severity=severity,
                risk_score=score,
                recommendation_id=recommendation_id,
                recommendation_text=rec.text if rec else plugin_finding.recommendation,
                evidence=plugin_finding.evidence,
                raw_data=plugin_finding.raw_data,
                check_status=plugin_finding.status.value,
                detected_at=plugin_finding.detected_at,
                category=plugin_finding.category,
                references=plugin_finding.reference_links or None,
                confidence=plugin_finding.confidence,
                cvss=plugin_finding.cvss,
                cwe=plugin_finding.cwe,
                cve=plugin_finding.cve,
            )

        fallback_severity = plugin_finding.severity or FindingSeverity.MEDIUM
        return ResolvedFinding(
            finding_code=rule_id,
            title=plugin_finding.title or rule_id.replace("_", " ").title(),
            description=plugin_finding.description or "No matching risk rule configured.",
            severity=fallback_severity,
            risk_score=points_for_severity(fallback_severity),
            recommendation_id=None,
            recommendation_text=plugin_finding.recommendation,
            evidence=plugin_finding.evidence,
            raw_data=plugin_finding.raw_data,
            check_status=plugin_finding.status.value,
            detected_at=plugin_finding.detected_at,
            category=plugin_finding.category,
            references=plugin_finding.reference_links or None,
            confidence=plugin_finding.confidence,
            cvss=plugin_finding.cvss,
            cwe=plugin_finding.cwe,
            cve=plugin_finding.cve,
        )

    def _open_findings(self, findings: list[Finding]) -> list[Finding]:
        return [f for f in findings if f.status == FindingStatus.OPEN]

    def _risk_points(self, findings: list[Finding]) -> list[float]:
        return [float(f.risk_score or 0.0) for f in self._open_findings(findings)]

    def build_breakdown(self, findings: list[Finding]) -> SeverityBreakdown:
        breakdown = SeverityBreakdown()
        for finding in self._open_findings(findings):
            setattr(breakdown, finding.severity.value, getattr(breakdown, finding.severity.value) + 1)
        return breakdown

    def prioritize_findings(self, findings: list[Finding], *, limit: int = 10) -> list[PrioritizedFinding]:
        open_findings = self._open_findings(findings)

        def sort_key(finding: Finding) -> tuple:
            criticality_rank = 99
            if finding.asset and finding.asset.criticality:
                order = {
                    AssetCriticality.CRITICAL: 0,
                    AssetCriticality.HIGH: 1,
                    AssetCriticality.MEDIUM: 2,
                    AssetCriticality.LOW: 3,
                }
                criticality_rank = order.get(finding.asset.criticality, 99)
            return (
                SEVERITY_SORT_ORDER.get(finding.severity, 99),
                -float(finding.risk_score or 0.0),
                criticality_rank,
            )

        ranked = sorted(open_findings, key=sort_key)
        return [
            PrioritizedFinding(
                finding_id=str(finding.id),
                finding_code=finding.finding_code or "",
                title=finding.title,
                severity=finding.severity,
                risk_score=float(finding.risk_score or 0.0),
                recommendation_id=finding.recommendation_id,
                asset_id=str(finding.asset_id),
                asset_criticality=(
                    finding.asset.criticality.value
                    if finding.asset and finding.asset.criticality
                    else None
                ),
            )
            for finding in ranked[:limit]
        ]

    def _score_bundle(self, findings: list[Finding]) -> tuple[float, float, str, str, SeverityBreakdown]:
        open_findings = self._open_findings(findings)
        risk_total = total_risk(self._risk_points(open_findings))
        sec_score = security_score(risk_total)
        return (
            risk_total,
            sec_score,
            grade_from_security_score(sec_score),
            risk_level_from_security_score(sec_score),
            self.build_breakdown(open_findings),
        )

    def calculate_asset_risk(
        self,
        db: Session,
        *,
        asset_id: uuid.UUID,
        scan_id: uuid.UUID | None = None,
        store: bool = True,
    ) -> AssetRiskResponse:
        findings = list_findings_for_asset(db, asset_id=asset_id)
        risk_total, sec_score, grade, _, breakdown = self._score_bundle(findings)

        if store:
            save_asset_risk(
                db,
                asset_id=asset_id,
                scan_id=scan_id,
                total_risk=risk_total,
                score=sec_score,
                grade=grade,
                breakdown=breakdown.model_dump(),
            )

        return AssetRiskResponse(
            asset_id=str(asset_id),
            scanned=True,
            scan_id=str(scan_id) if scan_id else None,
            total_risk=risk_total,
            score=sec_score,
            grade=grade,
            critical_count=breakdown.critical,
            high_count=breakdown.high,
            medium_count=breakdown.medium,
            low_count=breakdown.low,
            calculated_at=datetime.now(UTC),
        )

    def build_organization_asset_scores(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
    ) -> list[AssetRiskResponse]:
        assets = list_assets_for_organization(db, organization_id=organization_id)
        latest_by_asset = {
            row.asset_id: row
            for row in get_latest_asset_risks_for_organization(db, organization_id=organization_id)
        }
        scores: list[AssetRiskResponse] = []
        for asset in assets:
            record = latest_by_asset.get(asset.id)
            if record:
                scores.append(self._asset_risk_from_record(record))
            else:
                scores.append(unscanned_asset_risk(asset_id=str(asset.id)))
        return scores

    def calculate_organization_risk(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
        store: bool = True,
    ) -> OrganizationRiskResponse:
        asset_scores = self.build_organization_asset_scores(db, organization_id=organization_id)
        scanned = [a for a in asset_scores if a.scanned]
        unscanned_count = len(asset_scores) - len(scanned)

        if scanned:
            overall = sum(float(a.score or 0) for a in scanned) / len(scanned)
            org_total_risk = sum(float(a.total_risk or 0) for a in scanned)
            grade = grade_from_security_score(overall)
            risk_level = risk_level_from_security_score(overall)
        else:
            overall = None
            org_total_risk = None
            grade = None
            risk_level = None

        previous = get_previous_organization_score(db, organization_id=organization_id)
        trend = compute_trend(overall, previous) if overall is not None else "stable"

        if store and scanned:
            upsert_organization_risk(
                db,
                organization_id=organization_id,
                overall_score=overall,
                total_risk=org_total_risk or 0.0,
                grade=grade or "—",
                risk_level=risk_level or "Not assessed",
                trend=trend,
            )
            save_organization_risk_history(
                db,
                organization_id=organization_id,
                overall_score=overall,
                total_risk=org_total_risk or 0.0,
                grade=grade or "—",
            )
            if previous is not None and abs(overall - previous) >= 0.1:
                record_audit_event(
                    db,
                    action=AuditAction.ORG_RISK_SCORE_CHANGED,
                    organization_id=organization_id,
                    resource_type="organization",
                    resource_id=organization_id,
                    details={
                        "previous_score": round(previous, 1),
                        "current_score": round(overall, 1),
                        "trend": trend,
                    },
                )

        org_record = get_organization_risk(db, organization_id=organization_id)

        return OrganizationRiskResponse(
            organization_id=str(organization_id),
            overall_score=overall,
            total_risk=org_total_risk,
            grade=grade,
            risk_level=risk_level,
            trend=trend,
            scanned_assets=len(scanned),
            unscanned_assets=unscanned_count,
            asset_scores=asset_scores,
            updated_at=org_record.updated_at if org_record else datetime.now(UTC),
        )

    def calculate_project_risk(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        store: bool = True,
    ) -> ProjectRiskResponse:
        findings = list_findings_for_project(db, project_id=project_id)
        open_findings = self._open_findings(findings)
        risk_total, sec_score, grade, risk_level, breakdown = self._score_bundle(findings)
        top_issues = self.prioritize_findings(open_findings)

        if store:
            save_project_risk_metric(
                db,
                project_id=project_id,
                total_risk=risk_total,
                security_score=sec_score,
                grade=grade,
                risk_level=risk_level,
                open_findings=len(open_findings),
                breakdown=breakdown.model_dump(),
                top_issues=[issue.model_dump(mode="json") for issue in top_issues],
            )

        return ProjectRiskResponse(
            project_id=str(project_id),
            total_risk=risk_total,
            security_score=sec_score,
            grade=grade,
            risk_level=risk_level,
            open_findings=len(open_findings),
            breakdown=breakdown,
            top_issues=top_issues,
            calculated_at=datetime.now(UTC),
        )

    def recalculate_after_monitoring(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> None:
        self.calculate_asset_risk(db, asset_id=asset_id, store=True)
        self.calculate_project_risk(db, project_id=project_id, store=True)
        self.calculate_organization_risk(db, organization_id=organization_id, store=True)

    def recalculate_after_scan(
        self,
        db: Session,
        *,
        project_id: uuid.UUID,
        asset_id: uuid.UUID,
        scan_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> None:
        self.calculate_asset_risk(db, asset_id=asset_id, scan_id=scan_id, store=True)
        self.calculate_project_risk(db, project_id=project_id, store=True)
        self.calculate_organization_risk(db, organization_id=organization_id, store=True)

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
                total_risk=float(latest.total_risk),
                security_score=float(latest.security_score),
                grade=latest.grade,
                risk_level=latest.risk_level,
                open_findings=latest.open_findings,
                breakdown=SeverityBreakdown.model_validate(latest.breakdown or {}),
                top_issues=[
                    PrioritizedFinding.model_validate(item) for item in (latest.top_issues or [])
                ],
                calculated_at=latest.calculated_at,
            )
        return self.calculate_project_risk(db, project_id=project_id, store=True)

    def build_dashboard_metrics(
        self,
        db: Session,
        *,
        organization_id: uuid.UUID,
    ) -> DashboardMetrics:
        from app.scans.models import Scan

        findings = (
            db.query(Finding)
            .join(Asset, Asset.id == Finding.asset_id)
            .filter(Asset.organization_id == organization_id)
            .all()
        )
        open_findings = self._open_findings(findings)
        org = self.calculate_organization_risk(db, organization_id=organization_id, store=False)

        plugin_counts: Counter[str] = Counter()
        asset_type_counts: Counter[str] = Counter()
        issue_counts: Counter[str] = Counter()
        for finding in open_findings:
            if finding.plugin:
                plugin_counts[finding.plugin] += 1
            if finding.finding_code:
                issue_counts[finding.finding_code] += 1
            asset = finding.asset
            if asset:
                asset_type_counts[
                    asset.type.value if hasattr(asset.type, "value") else str(asset.type)
                ] += 1

        assets_at_risk = sum(
            1 for a in org.asset_scores if a.scanned and a.score is not None and a.score < 75
        )
        most_common = issue_counts.most_common(1)[0][0] if issue_counts else None

        scans = (
            db.query(Scan)
            .join(Asset, Asset.id == Scan.asset_id)
            .filter(Asset.organization_id == organization_id, Scan.completed_at.isnot(None))
            .order_by(Scan.completed_at.asc())
            .all()
        )
        avg_days: float | None = None
        if len(scans) >= 2:
            gaps = []
            for i in range(1, len(scans)):
                if scans[i].completed_at and scans[i - 1].completed_at:
                    delta = scans[i].completed_at - scans[i - 1].completed_at
                    gaps.append(delta.total_seconds() / 86400)
            if gaps:
                avg_days = round(sum(gaps) / len(gaps), 1)

        history = list_organization_risk_history(db, organization_id=organization_id, limit=30)
        trend_points = [
            RiskTrendPoint(
                date=entry.calculated_at,
                security_score=float(entry.overall_score),
                grade=entry.grade,
                total_risk=float(entry.total_risk),
            )
            for entry in history
        ]

        breakdown = self.build_breakdown(open_findings)
        return DashboardMetrics(
            overall_security_score=org.overall_score,
            organization_grade=org.grade,
            risk_level=org.risk_level,
            trend=org.trend,
            total_findings=len(open_findings),
            critical_findings=breakdown.critical,
            high_findings=breakdown.high,
            assets_at_risk=assets_at_risk,
            unscanned_assets=org.unscanned_assets,
            most_common_issue=most_common,
            average_days_between_scans=avg_days,
            findings_by_plugin=dict(plugin_counts),
            findings_by_asset_type=dict(asset_type_counts),
            risk_trend=trend_points,
        )


risk_engine = RiskEngine()
