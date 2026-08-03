from pydantic import Field, field_validator

from app.shared.schemas.base import BaseSchema


class ProjectSummary(BaseSchema):
    id: str
    organization_id: str
    name: str
    slug: str
    description: str | None = None
    created_by: str | None = None
    is_active: bool


class CreateProjectRequest(BaseSchema):
    name: str = Field(min_length=1, max_length=255)
    slug: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value


class UpdateProjectRequest(BaseSchema):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    is_active: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def trim_name(cls, value: str | None) -> str | None:
        if isinstance(value, str):
            trimmed = value.strip()
            return trimmed or None
        return value
