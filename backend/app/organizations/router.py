import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.members.models import OrganizationMember
from app.users.models import User
from app.organizations.schemas import CreateOrganizationRequest, UpdateOrganizationRequest
from app.organizations.services.organization_service import (
    archive_current_organization,
    create_user_organization,
    delete_current_organization,
    get_current_organization,
    list_user_organizations,
    restore_archived_organization,
    update_current_organization,
)
from app.audit.router import router as audit_router
from app.dashboard.router import router as dashboard_router
from app.organizations.services.activity_service import get_organization_activity
from app.organizations.services.overview_service import get_organization_overview
from app.reports.org_router import router as org_reports_router
from app.risk.organization_router import router as org_risk_router
from app.monitoring.org_router import router as org_monitoring_router

router = APIRouter()
router.include_router(org_risk_router, prefix="/risk", tags=["organization-risk"])
router.include_router(dashboard_router, prefix="/current/dashboard", tags=["dashboard"])
router.include_router(org_reports_router, prefix="/current/reports", tags=["organization-reports"])
router.include_router(
    org_monitoring_router,
    prefix="/current/monitoring",
    tags=["organization-monitoring"],
)
router.include_router(audit_router, tags=["audit"])


@router.get("/me")
def list_my_organizations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    organizations = list_user_organizations(db, current_user)
    return success_response(
        data={
            "items": [org.model_dump(mode="json") for org in organizations],
            "total": len(organizations),
        }
    )


@router.post("", status_code=201)
def create_organization(
    body: CreateOrganizationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    organization = create_user_organization(db, current_user, body=body)
    return success_response(data=organization.model_dump(mode="json"), status_code=201)


@router.get("/current")
def get_organization(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> JSONResponse:
    organization = get_current_organization(db, membership)
    return success_response(data=organization.model_dump(mode="json"))


@router.get("/current/overview")
def get_organization_overview_route(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> JSONResponse:
    overview = get_organization_overview(db, membership)
    return success_response(data=overview.model_dump(mode="json"))


@router.get("/current/activity")
def get_organization_activity_route(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    action: str | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    actor: str | None = Query(default=None),
    asset_id: uuid.UUID | None = Query(default=None),
    severity: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_READ)),
) -> JSONResponse:
    activity = get_organization_activity(
        db,
        organization_id=membership.organization_id,
        page=page,
        limit=limit,
        action=action,
        user_id=user_id,
        actor=actor,
        asset_id=asset_id,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
    )
    return success_response(data=activity.model_dump(mode="json"))


@router.patch("/current")
def patch_organization(
    body: UpdateOrganizationRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_UPDATE)),
) -> JSONResponse:
    organization = update_current_organization(db, membership, body=body)
    return success_response(data=organization.model_dump(mode="json"))


@router.patch("/current/archive")
def archive_organization(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_DELETE)),
) -> JSONResponse:
    organization = archive_current_organization(db, membership)
    return success_response(data=organization.model_dump(mode="json"))


@router.patch("/{organization_id}/restore")
def restore_organization_route(
    organization_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    organization = restore_archived_organization(
        db,
        user=current_user,
        organization_id=organization_id,
    )
    return success_response(data=organization.model_dump(mode="json"))


@router.delete("/current", status_code=200)
def delete_organization(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_DELETE)),
) -> JSONResponse:
    delete_current_organization(db, membership)
    return success_response(data={"message": "Organization deleted successfully"})
