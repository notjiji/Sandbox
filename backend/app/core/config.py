from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        case_sensitive=True,
        extra="ignore",
    )

    POSTGRES_HOST: str
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    SECRET_KEY: str
    JWT_SECRET: str
    REDIS_URL: str
    OPENAI_API_KEY: str = ""
    AI_MODEL: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.2
    AI_MAX_OUTPUT_TOKENS: int = 2048
    AI_REQUEST_TIMEOUT_SECONDS: float = 60.0
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:80,http://127.0.0.1:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_SECONDS: int = 900
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 1
    ORGANIZATION_INVITE_EXPIRE_DAYS: int = 7
    EMAIL_VERIFICATION_OTP_EXPIRE_MINUTES: int = 15
    EMAIL_VERIFICATION_OTP_MAX_ATTEMPTS: int = 5

    ACCOUNT_LOCKOUT_MAX_ATTEMPTS: int = 5
    ACCOUNT_LOCKOUT_WINDOW_SECONDS: int = 900
    ACCOUNT_LOCKOUT_DURATION_SECONDS: int = 900

    FRONTEND_URL: str = "http://localhost"

    SCAN_RUN_INLINE: bool | None = None

    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "Sandbox <onboarding@resend.dev>"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("SECRET_KEY", "JWT_SECRET")
    @classmethod
    def validate_secret_length(cls, value: str, info) -> str:
        if len(value) < 32:
            msg = f"{info.field_name} must be at least 32 characters"
            raise ValueError(msg)
        return value

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.SCAN_RUN_INLINE is None:
            object.__setattr__(self, "SCAN_RUN_INLINE", self.ENVIRONMENT == "development")

        if self.ENVIRONMENT != "production":
            return self

        if self.SECRET_KEY.startswith("change-me") or self.JWT_SECRET.startswith("change-me"):
            raise ValueError("Production requires non-default SECRET_KEY and JWT_SECRET values")

        if "changeme" in self.POSTGRES_PASSWORD.lower():
            raise ValueError("Production requires a non-default POSTGRES_PASSWORD")

        if not self.RESEND_API_KEY:
            raise ValueError("Production requires RESEND_API_KEY for transactional email")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
