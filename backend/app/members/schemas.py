from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.core.rbac import ROLE_DESCRIPTIONS, get_permissions_for_role
from app.members.enums import MemberStatus, OrganizationRole
from app.auth.schemas import normalize_email
from app.shared.schemas.base import BaseSchema


class RoleInfo(BaseSchema):
    role: OrganizationRole
    description: str
    permissions: list[str]


class RolesListResponse(BaseSchema):
    roles: list[RoleInfo]


def build_roles_list_response() -> RolesListResponse:
    roles = [
        RoleInfo(
            role=role,
            description=ROLE_DESCRIPTIONS[role],
            permissions=sorted(p.value for p in get_permissions_for_role(role)),
        )
        for role in OrganizationRole
    ]
    return RolesListResponse(roles=roles)


class MemberSummary(BaseSchema):
    membership_id: str
    user_id: str
    email: str
    first_name: str
    last_name: str
    role: OrganizationRole
    status: MemberStatus
    joined_at: datetime | None = None


class InviteMemberRequest(BaseSchema):
    email: EmailStr
    role: OrganizationRole = OrganizationRole.VIEWER

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_email(value)
        return value

    @field_validator("role")
    @classmethod
    def validate_invite_role(cls, value: OrganizationRole) -> OrganizationRole:
        if value == OrganizationRole.OWNER:
            raise ValueError("Use ownership transfer to assign the owner role")
        return value


class UpdateMemberRoleRequest(BaseSchema):
    role: OrganizationRole | None = None
    status: MemberStatus | None = None

    @field_validator("role")
    @classmethod
    def validate_update_role(cls, value: OrganizationRole | None) -> OrganizationRole | None:
        if value == OrganizationRole.OWNER:
            raise ValueError("Use ownership transfer to assign the owner role")
        return value


class TransferOwnershipRequest(BaseSchema):
    new_owner_user_id: str = Field(min_length=1)


class InviteResult(BaseSchema):
    invite_id: str
    email: str
    role: OrganizationRole
    status: str
    user_exists: bool
    membership_id: str | None = None


class PendingInviteSummary(BaseSchema):
    invite_id: str
    email: str
    role: OrganizationRole
    status: str
    invited_at: datetime
    expires_at: datetime
    membership_id: str | None = None


class InvitePreview(BaseSchema):
    organization_id: str
    organization_name: str
    organization_slug: str
    email: str
    role: OrganizationRole
    inviter_name: str
    expires_at: datetime
    user_exists: bool
