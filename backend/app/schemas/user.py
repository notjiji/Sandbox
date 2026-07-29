from pydantic import Field, field_validator

from app.schemas.base import BaseSchema


class UserProfileResponse(BaseSchema):
    id: str
    first_name: str
    last_name: str
    email: str
    is_verified: bool
    role: str | None = None
    organization: str | None = None


class UpdateUserProfileRequest(BaseSchema):
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def trim_names(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value
