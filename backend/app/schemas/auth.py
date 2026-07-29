import re

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema

PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>\[\]/_+=\-]).+$"
)


def normalize_email(value: str) -> str:
    return value.strip().lower()


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_email(value)
        return value


class RegisterRequest(BaseSchema):
    first_name: str = Field(min_length=1, max_length=128)
    last_name: str = Field(min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("first_name", "last_name", mode="before")
    @classmethod
    def trim_names(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_email(value)
        return value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < PASSWORD_MIN_LENGTH:
            raise ValueError(f"Password must be at least {PASSWORD_MIN_LENGTH} characters")
        if not PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Password must include uppercase, lowercase, number, and special character"
            )
        return value


class RefreshRequest(BaseSchema):
    refresh_token: str = Field(min_length=1)


class LogoutRequest(BaseSchema):
    refresh_token: str = Field(min_length=1)


class ForgotPasswordRequest(BaseSchema):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_email(value)
        return value


class RegisterResponse(BaseSchema):
    message: str


class LoginResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int


class RefreshResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int


class LogoutResponse(BaseSchema):
    message: str
