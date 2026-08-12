from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.monitoring.services.monitoring_service import get_organization_monitoring

router = APIRouter()


@router.get("/overview")
def organization_monitoring_overview(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MONITORING_READ)),
) -> JSONResponse:
    overview = get_organization_monitoring(db, membership)
    return success_response(data=overview.model_dump(mode="json"))
