import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.risk.service import risk_service

router = APIRouter()


@router.get("")
def get_project_risk(
    project_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.FINDING_READ)),
) -> JSONResponse:
    result = risk_service.calculate_project_risk(db, membership, project_id=project_id)
    return success_response(data=result.model_dump(mode="json"))
