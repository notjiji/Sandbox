import re

from pydantic import EmailStr, Field, field_validator

from app.schemas.base import BaseSchema

PASSWORD_MIN_LENGTH = 8
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d).+$")


class LoginRequest(BaseSchema):
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)


class RegisterRequest(BaseSchema):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)
    confirm_password: str = Field(min_length=PASSWORD_MIN_LENGTH, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if not PASSWORD_PATTERN.match(value):
            raise ValueError("Password must contain at least one letter and one number")
        return value

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, value: str, info) -> str:
        password = info.data.get("password")
        if password and value != password:
            raise ValueError("Passwords do not match")
        return value


class ForgotPasswordRequest(BaseSchema):
    email: EmailStr
