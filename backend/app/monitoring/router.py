import uuid

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.monitoring.enums import DEFAULT_HISTORY_HOURS, MAX_HISTORY_HOURS
from app.monitoring.services.enrollment_service import enroll_agent, revoke_agent
from app.monitoring.services.monitoring_service import get_asset_monitoring

router = APIRouter()


@router.get("")
def get_monitoring(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    hours: int = Query(default=DEFAULT_HISTORY_HOURS, ge=1, le=MAX_HISTORY_HOURS),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MONITORING_READ)),
) -> JSONResponse:
    overview = get_asset_monitoring(
        db, membership, project_id=project_id, asset_id=asset_id, hours=hours
    )
    return success_response(data=overview.model_dump(mode="json"))


@router.post("/enroll", status_code=201)
def enroll_monitoring_agent(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MONITORING_MANAGE)),
) -> JSONResponse:
    enrollment = enroll_agent(db, membership, project_id=project_id, asset_id=asset_id)
    return success_response(data=enrollment.model_dump(mode="json"), status_code=201)


@router.post("/revoke")
def revoke_monitoring_agent(
    project_id: uuid.UUID,
    asset_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MONITORING_MANAGE)),
) -> JSONResponse:
    revoke_agent(db, membership, project_id=project_id, asset_id=asset_id)
    return success_response(data={"message": "Agent revoked"})
