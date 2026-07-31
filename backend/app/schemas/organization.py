from datetime import datetime

from pydantic import EmailStr, Field, field_validator

from app.models.organization_member import MemberStatus, OrganizationRole
from app.schemas.auth import normalize_email
from app.schemas.base import BaseSchema


class OrganizationSummary(BaseSchema):
    id: str
    name: str
    slug: str
    role: OrganizationRole
    membership_status: MemberStatus
    is_active: bool


class OrganizationDetail(BaseSchema):
    id: str
    name: str
    slug: str
    description: str | None = None
    industry: str | None = None
    website: str | None = None
    logo_url: str | None = None
    country: str | None = None
    timezone: str | None = None
    created_by: str | None = None
    is_active: bool


class CreateOrganizationRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    industry: str | None = Field(default=None, max_length=128)
    website: str | None = Field(default=None, max_length=512)
    logo_url: str | None = Field(default=None, max_length=1024)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class UpdateOrganizationRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    industry: str | None = Field(default=None, max_length=128)
    website: str | None = Field(default=None, max_length=512)
    logo_url: str | None = Field(default=None, max_length=1024)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = Field(default=None, max_length=64)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value


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
