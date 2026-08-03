from pydantic import Field, field_validator

from app.members.enums import MemberStatus, OrganizationRole
from app.shared.schemas.base import BaseSchema


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
