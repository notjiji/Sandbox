import uuid

from sqlalchemy.orm import Session

from app.findings.enums import FindingStatus
from app.findings.repositories.finding_repository import list_findings_for_project
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.risk.calculator import RiskCalculator
from app.risk.schemas import ProjectRiskResponse, SeverityBreakdown


class RiskService:
    def __init__(self) -> None:
        self._calculator = RiskCalculator()

    def calculate_project_risk(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
    ) -> ProjectRiskResponse:
        require_active_project(db, membership, project_id)
        findings = list_findings_for_project(db, project_id=project_id)
        open_findings = [f for f in findings if f.status == FindingStatus.OPEN]

        breakdown = SeverityBreakdown()
        payload = []
        for finding in open_findings:
            severity = finding.severity.value
            setattr(breakdown, severity, getattr(breakdown, severity) + 1)
            item = {"severity": severity}
            if finding.asset and finding.asset.criticality:
                item["criticality"] = finding.asset.criticality.value
            payload.append(item)

        score = self._calculator.score_findings(payload)
        return ProjectRiskResponse(
            project_id=str(project_id),
            score=score,
            open_findings=len(open_findings),
            breakdown=breakdown,
        )


risk_service = RiskService()
