import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.service import search_organization_audit_logs
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember

router = APIRouter()


@router.get("/current/audit-logs")
def search_audit_logs_route(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    actor: str | None = Query(default=None, description="Match actor name or email"),
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    asset_id: uuid.UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> JSONResponse:
    result = search_organization_audit_logs(
        db,
        organization_id=membership.organization_id,
        page=page,
        limit=limit,
        action=action,
        user_id=user_id,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(data=result.model_dump(mode="json"))
