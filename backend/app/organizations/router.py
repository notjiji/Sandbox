from fastapi import APIRouter, Depends
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
    create_user_organization,
    delete_current_organization,
    get_current_organization,
    list_user_organizations,
    update_current_organization,
)
from app.risk.organization_router import router as org_risk_router

router = APIRouter()
router.include_router(org_risk_router, prefix="/risk", tags=["organization-risk"])


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


@router.patch("/current")
def patch_organization(
    body: UpdateOrganizationRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_UPDATE)),
) -> JSONResponse:
    organization = update_current_organization(db, membership, body=body)
    return success_response(data=organization.model_dump(mode="json"))


@router.delete("/current", status_code=200)
def delete_organization(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.ORG_DELETE)),
) -> JSONResponse:
    delete_current_organization(db, membership)
    return success_response(data={"message": "Organization deleted successfully"})
