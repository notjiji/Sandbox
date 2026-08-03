import uuid

from sqlalchemy.orm import Session

from app.core.risk_engine.engine import risk_engine
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.risk.repositories.risk_repository import get_organization_risk
from app.risk.schemas import DashboardMetrics, OrganizationRiskResponse, ProjectRiskResponse


class RiskService:
    def calculate_project_risk(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        project_id: uuid.UUID,
        refresh: bool = False,
    ) -> ProjectRiskResponse:
        require_active_project(db, membership, project_id)
        if refresh:
            result = risk_engine.calculate_project_risk(db, project_id=project_id, store=True)
            db.commit()
            return result
        return risk_engine.get_or_calculate_project_risk(db, project_id=project_id)

    def calculate_organization_risk(
        self,
        db: Session,
        membership: OrganizationMember,
        *,
        refresh: bool = False,
    ) -> OrganizationRiskResponse:
        org_id = membership.organization_id
        if refresh or get_organization_risk(db, organization_id=org_id) is None:
            result = risk_engine.calculate_organization_risk(db, organization_id=org_id, store=True)
            db.commit()
            return result
        return risk_engine.calculate_organization_risk(db, organization_id=org_id, store=False)

    def get_dashboard_metrics(
        self,
        db: Session,
        membership: OrganizationMember,
    ) -> DashboardMetrics:
        risk_engine.calculate_organization_risk(
            db, organization_id=membership.organization_id, store=True
        )
        metrics = risk_engine.build_dashboard_metrics(
            db, organization_id=membership.organization_id
        )
        db.commit()
        return metrics


risk_service = RiskService()
