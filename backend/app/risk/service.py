import uuid

from sqlalchemy.orm import Session

from app.core.risk_engine.engine import risk_engine
from app.members.models import OrganizationMember
from app.projects.validators import require_active_project
from app.risk.schemas import ProjectRiskResponse


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


risk_service = RiskService()
