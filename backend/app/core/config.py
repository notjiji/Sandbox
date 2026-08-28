from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.production_config import validate_production_settings as run_production_validation


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
    AI_ENABLED: bool | None = None
    AI_MODEL: str = "gpt-4o-mini"
    AI_TEMPERATURE: float = 0.2
    AI_MAX_OUTPUT_TOKENS: int = 2048
    AI_REQUEST_TIMEOUT_SECONDS: float = 60.0
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False
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
    PUBLIC_API_URL: str = "http://localhost:8000/api/v1"
    AGENT_ENROLLMENT_TOKEN_EXPIRE_MINUTES: int = 15

    SCAN_RUN_INLINE: bool | None = None
    REPORT_RUN_INLINE: bool | None = None

    SCAN_TASK_SOFT_TIMEOUT_SECONDS: int = 3300
    SCAN_TASK_HARD_TIMEOUT_SECONDS: int = 3600
    SCAN_STALE_RUNNING_SECONDS: int = 3900
    REPORT_TASK_SOFT_TIMEOUT_SECONDS: int = 600
    REPORT_TASK_HARD_TIMEOUT_SECONDS: int = 900
    REPORT_STALE_GENERATING_SECONDS: int = 1200
    CELERY_BEAT_PIDFILE: str = "/tmp/celerybeat.pid"

    RESEND_API_KEY: str = ""
    RESEND_FROM: str = "Sandbox <onboarding@resend.dev>"

    AUDIT_SIEM_SINK: str = "none"
    AUDIT_SYSLOG_HOST: str = ""
    AUDIT_SYSLOG_PORT: int = 514
    AUDIT_SYSLOG_PROTOCOL: str = "udp"
    AUDIT_SPLUNK_HEC_URL: str = ""
    AUDIT_SPLUNK_HEC_TOKEN: str = ""
    AUDIT_ELK_URL: str = ""
    AUDIT_ELK_INDEX: str = "sandbox-audit"
    AUDIT_ELK_API_KEY: str = ""
    AUDIT_SENTINEL_WORKSPACE_ID: str = ""
    AUDIT_SENTINEL_SHARED_KEY: str = ""
    AUDIT_SENTINEL_LOG_TYPE: str = "SandboxAudit"

    REPORT_STORAGE_BACKEND: Literal["local", "s3"] = "local"
    REPORT_STORAGE_PATH: str = "/app/storage/reports"
    REPORT_S3_BUCKET: str = ""
    REPORT_S3_PREFIX: str = ""
    REPORT_S3_REGION: str = "us-east-1"
    REPORT_S3_ENDPOINT_URL: str = ""
    REPORT_S3_ACCESS_KEY_ID: str = ""
    REPORT_S3_SECRET_ACCESS_KEY: str = ""

    BACKUP_ENCRYPTION_PASSPHRASE: str = ""
    BACKUP_RETENTION_DAYS: int = 7
    BACKUP_REPORT_FILES: bool = True
    BACKUP_S3_URI: str = ""

    @property
    def ai_live_enabled(self) -> bool:
        return bool(self.AI_ENABLED and self.OPENAI_API_KEY.strip())

    @property
    def report_storage_root_path(self) -> Path:
        return Path(self.REPORT_STORAGE_PATH)

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
        if self.REPORT_RUN_INLINE is None:
            object.__setattr__(self, "REPORT_RUN_INLINE", self.ENVIRONMENT == "development")
        if self.AI_ENABLED is None:
            object.__setattr__(self, "AI_ENABLED", self.ENVIRONMENT != "production")

        if self.ENVIRONMENT != "production":
            return self

        run_production_validation(self)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
