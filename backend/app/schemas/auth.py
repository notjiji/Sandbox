from pydantic import EmailStr, Field, field_validator

from app.core.password import (
    PASSWORD_MAX_LENGTH,
    PASSWORD_MIN_LENGTH,
    validate_password_strength,
)
from app.schemas.base import BaseSchema


def normalize_email(value: str) -> str:
    return value.strip().lower()


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)

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
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)
    invite_token: str | None = Field(default=None, min_length=1)

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
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
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
    email: str


class VerifyEmailRequest(BaseSchema):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_email(value)
        return value


class ResendVerificationRequest(BaseSchema):
    email: EmailStr

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, value: str) -> str:
        if isinstance(value, str):
            return normalize_email(value)
        return value


class LoginResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int
    session_id: str


class RefreshResponse(BaseSchema):
    access_token: str
    refresh_token: str
    expires_in: int
    session_id: str


class LogoutResponse(BaseSchema):
    message: str


class ForgotPasswordResponse(BaseSchema):
    message: str


class ResetPasswordRequest(BaseSchema):
    token: str = Field(min_length=1)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class ChangePasswordRequest(BaseSchema):
    current_password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)
    new_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        validate_password_strength(value)
        return value


class MessageResponse(BaseSchema):
    message: str
