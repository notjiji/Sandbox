import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.audit.service import (
    export_organization_audit_logs,
    get_organization_audit_log,
    search_organization_audit_logs,
    verify_organization_audit_chain,
)
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember

router = APIRouter()


def _list_query(
    page: int,
    limit: int,
    action: str | None,
    user_id: uuid.UUID | None,
    actor: str | None,
    entity_type: str | None,
    entity_id: uuid.UUID | None,
    asset_id: uuid.UUID | None,
    severity: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
    db: Session,
    membership: OrganizationMember,
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


@router.get("")
def list_audit_logs(
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
    return _list_query(
        page,
        limit,
        action,
        user_id,
        actor,
        entity_type,
        entity_id,
        asset_id,
        severity,
        date_from,
        date_to,
        db,
        membership,
    )


@router.get("/export")
def export_audit_logs(
    fmt: str = Query(default="csv", alias="format"),
    action: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    actor: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    asset_id: uuid.UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> Response:
    return export_organization_audit_logs(
        db,
        organization_id=membership.organization_id,
        fmt=fmt,
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


@router.get("/integrity")
def audit_log_integrity(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> JSONResponse:
    result = verify_organization_audit_chain(db, organization_id=membership.organization_id)
    return success_response(data=result.model_dump(mode="json"))


@router.get("/{log_id}")
def get_audit_log(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> JSONResponse:
    result = get_organization_audit_log(
        db,
        organization_id=membership.organization_id,
        log_id=log_id,
    )
    return success_response(data=result.model_dump(mode="json"))
