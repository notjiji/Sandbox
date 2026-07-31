import uuid

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_membership_any_status, get_current_user, require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.core.responses import success_response
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.schemas.organization import (
    CreateOrganizationRequest,
    InviteMemberRequest,
    TransferOwnershipRequest,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)
from app.schemas.rbac import build_roles_list_response
from app.services.organization import (
    accept_invitation,
    accept_invite_by_token,
    create_user_organization,
    delete_current_organization,
    get_current_organization,
    get_invite_preview,
    invite_member,
    list_current_organization_members,
    list_current_pending_invites,
    list_user_organizations,
    remove_member,
    revoke_invite,
    transfer_organization_ownership,
    update_current_organization,
    update_member,
)

router = APIRouter()


@router.get("/roles")
def list_roles() -> JSONResponse:
    response = build_roles_list_response()
    return JSONResponse(status_code=200, content=response.model_dump(mode="json"))


@router.get("/invites/{token}")
def preview_invite(
    token: str,
    db: Session = Depends(get_db),
) -> JSONResponse:
    preview = get_invite_preview(db, token=token)
    return success_response(data=preview.model_dump(mode="json"))


@router.post("/invites/{token}/accept")
def accept_invite_token(
    token: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JSONResponse:
    organization = accept_invite_by_token(db, user=current_user, token=token)
    return success_response(data=organization.model_dump(mode="json"))


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


@router.get("/current/members")
def list_members(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_READ)),
) -> JSONResponse:
    members = list_current_organization_members(db, membership)
    return success_response(
        data={
            "items": [member.model_dump(mode="json") for member in members],
            "total": len(members),
        }
    )


@router.get("/current/invites")
def list_pending_invites(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_READ)),
) -> JSONResponse:
    invites = list_current_pending_invites(db, membership)
    return success_response(
        data={
            "items": [invite.model_dump(mode="json") for invite in invites],
            "total": len(invites),
        }
    )


@router.post("/current/members/accept")
def accept_organization_invitation(
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(get_current_membership_any_status),
) -> JSONResponse:
    member = accept_invitation(db, membership)
    return success_response(data=member.model_dump(mode="json"))


@router.post("/current/members", status_code=201)
def invite_organization_member(
    body: InviteMemberRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_INVITE)),
) -> JSONResponse:
    result = invite_member(db, membership, body=body)
    return success_response(data=result.model_dump(mode="json"), status_code=201)


@router.delete("/current/invites/{invite_id}", status_code=200)
def delete_pending_invite(
    invite_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_INVITE)),
) -> JSONResponse:
    revoke_invite(db, membership, invite_id=invite_id)
    return success_response(data={"message": "Invitation revoked successfully"})


@router.patch("/current/members/{membership_id}")
def patch_member_role(
    membership_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_UPDATE)),
) -> JSONResponse:
    member = update_member(
        db,
        membership,
        target_membership_id=membership_id,
        body=body,
    )
    return success_response(data=member.model_dump(mode="json"))


@router.delete("/current/members/{membership_id}", status_code=200)
def delete_member(
    membership_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_REMOVE)),
) -> JSONResponse:
    remove_member(db, membership, target_membership_id=membership_id)
    return success_response(data={"message": "Member removed successfully"})


@router.post("/current/transfer-ownership")
def transfer_ownership(
    body: TransferOwnershipRequest,
    db: Session = Depends(get_db),
    membership: OrganizationMember = Depends(require_permission(Permission.MEMBER_TRANSFER_OWNERSHIP)),
) -> JSONResponse:
    member = transfer_organization_ownership(db, membership, body=body)
    return success_response(data=member.model_dump(mode="json"))
