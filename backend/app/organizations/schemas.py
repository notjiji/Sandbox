from pydantic import Field, field_validator

from app.members.enums import MemberStatus, OrganizationRole
from app.auth.schemas import normalize_email
from app.shared.schemas.base import BaseSchema


class NotificationSettings(BaseSchema):
    email_enabled: bool = True
    weekly_reports: bool = True
    scan_complete: bool = True
    critical_findings: bool = True


class SecuritySettings(BaseSchema):
    mfa_policy: str = "optional"
    password_min_length: int = Field(default=12, ge=8, le=128)
    session_timeout_minutes: int = Field(default=480, ge=15, le=1440)


class ReportBrandingSettings(BaseSchema):
    primary_color: str = Field(default="#7c3aed", pattern=r"^#[0-9A-Fa-f]{6}$")
    contact_email: str | None = Field(default=None, max_length=255)
    footer_text: str | None = Field(default=None, max_length=500)


class OrganizationSettings(BaseSchema):
    language: str = "en"
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    branding: ReportBrandingSettings = Field(default_factory=ReportBrandingSettings)


class OrganizationSummary(BaseSchema):
    id: str
    name: str
    slug: str
    logo_url: str | None = None
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
    settings: OrganizationSettings = Field(default_factory=OrganizationSettings)
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


class UpdateOrganizationSettings(BaseSchema):
    language: str | None = None
    notifications: NotificationSettings | None = None
    security: SecuritySettings | None = None
    branding: ReportBrandingSettings | None = None


class UpdateOrganizationRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    industry: str | None = Field(default=None, max_length=128)
    website: str | None = Field(default=None, max_length=512)
    logo_url: str | None = Field(default=None, max_length=1024)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = Field(default=None, max_length=64)
    settings: UpdateOrganizationSettings | None = None

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value
