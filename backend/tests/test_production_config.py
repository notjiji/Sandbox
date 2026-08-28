"""Production configuration validation tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.production_config import (
    collect_production_config_errors,
    is_localhost_url,
    is_weak_database_password,
    is_weak_secret,
)


def _production_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "POSTGRES_HOST": "postgres",
        "POSTGRES_DB": "sandbox",
        "POSTGRES_USER": "sandbox",
        "POSTGRES_PASSWORD": "prod-db-credential-x7k9m2n4p8q1r5t3",
        "SECRET_KEY": "production-secret-key-minimum-thirty-two-characters",
        "JWT_SECRET": "production-jwt-secret-minimum-thirty-two-characters",
        "REDIS_URL": "redis://redis:6379/0",
        "ENVIRONMENT": "production",
        "DEBUG": False,
        "LOG_LEVEL": "INFO",
        "CORS_ORIGINS": "https://app.example.com",
        "FRONTEND_URL": "https://app.example.com",
        "PUBLIC_API_URL": "https://app.example.com/api/v1",
        "RESEND_API_KEY": "re_production_live_email_api_key_value",
        "BACKUP_ENCRYPTION_PASSPHRASE": "production-backup-passphrase-minimum-32-chars",
        "SCAN_RUN_INLINE": False,
        "REPORT_RUN_INLINE": False,
        "AI_ENABLED": False,
        "OPENAI_API_KEY": "",
    }
    base.update(overrides)
    return base


def test_valid_production_settings_load() -> None:
    settings = Settings(**_production_kwargs())
    assert settings.ENVIRONMENT == "production"
    assert settings.AI_ENABLED is False
    assert settings.ai_live_enabled is False


@pytest.mark.parametrize(
    ("field", "value", "fragment"),
    [
        ("DEBUG", True, "DEBUG=false"),
        ("LOG_LEVEL", "DEBUG", "LOG_LEVEL"),
        ("CORS_ORIGINS", "http://localhost:5173", "localhost"),
        ("FRONTEND_URL", "http://localhost", "FRONTEND_URL"),
        ("PUBLIC_API_URL", "http://127.0.0.1/api/v1", "PUBLIC_API_URL"),
        ("SECRET_KEY", "change-me-insecure-secret-key-value-here", "SECRET_KEY"),
        ("POSTGRES_PASSWORD", "changeme", "POSTGRES_PASSWORD"),
        ("SCAN_RUN_INLINE", True, "SCAN_RUN_INLINE"),
        ("AI_ENABLED", True, "OPENAI_API_KEY"),
    ],
)
def test_production_rejects_invalid_values(field: str, value: object, fragment: str) -> None:
    kwargs = _production_kwargs(**{field: value})
    with pytest.raises(ValidationError) as exc:
        Settings(**kwargs)
    assert fragment in str(exc.value)


def test_production_allows_ai_when_key_present() -> None:
    settings = Settings(
        **_production_kwargs(
            AI_ENABLED=True,
            OPENAI_API_KEY="sk-production-live-openai-key-placeholder-1234567890",
        )
    )
    assert settings.ai_live_enabled is True


def test_production_defaults_ai_disabled() -> None:
    settings = Settings(**_production_kwargs(AI_ENABLED=None))
    assert settings.AI_ENABLED is False


def test_development_allows_localhost_cors() -> None:
    settings = Settings(
        POSTGRES_HOST="localhost",
        POSTGRES_DB="sandbox_test",
        POSTGRES_USER="sandbox",
        POSTGRES_PASSWORD="changeme-in-dev-only-32chars",
        SECRET_KEY="test-secret-key-at-least-thirty-two-characters-long",
        JWT_SECRET="test-jwt-secret-at-least-thirty-two-characters-long",
        REDIS_URL="redis://localhost:6379/0",
        ENVIRONMENT="development",
        CORS_ORIGINS="http://localhost:5173",
        FRONTEND_URL="http://localhost",
    )
    assert settings.ENVIRONMENT == "development"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost:5173", True),
        ("https://app.example.com", False),
        ("http://127.0.0.1:8000", True),
    ],
)
def test_is_localhost_url(url: str, expected: bool) -> None:
    assert is_localhost_url(url) is expected


def test_is_weak_secret_detects_placeholders() -> None:
    assert is_weak_secret("change-me-not-long-enough")
    assert not is_weak_secret("production-secret-key-minimum-thirty-two-characters")


def test_is_weak_database_password() -> None:
    assert is_weak_database_password("changeme")
    assert not is_weak_database_password("prod-db-credential-x7k9m2n4p8q1r5t3")


def test_collect_production_config_errors_reports_multiple_issues() -> None:
    settings = Settings(**_production_kwargs())
    settings.DEBUG = True
    settings.CORS_ORIGINS = "http://localhost"
    settings.AI_ENABLED = True
    settings.OPENAI_API_KEY = ""
    errors = collect_production_config_errors(settings)
    assert any("DEBUG" in item for item in errors)
    assert any("CORS_ORIGINS" in item for item in errors)
    assert any("OPENAI_API_KEY" in item for item in errors)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
