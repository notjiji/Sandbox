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
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    LOG_LEVEL: str = "INFO"

    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:80,http://127.0.0.1:5173"
    CORS_ALLOW_CREDENTIALS: bool = True
    RATE_LIMIT_DEFAULT: str = "100/minute"
    RATE_LIMIT_AUTH: str = "10/minute"

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
        if self.ENVIRONMENT != "production":
            return self

        if self.SECRET_KEY.startswith("change-me") or self.JWT_SECRET.startswith("change-me"):
            raise ValueError("Production requires non-default SECRET_KEY and JWT_SECRET values")

        if "changeme" in self.POSTGRES_PASSWORD.lower():
            raise ValueError("Production requires a non-default POSTGRES_PASSWORD")

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
