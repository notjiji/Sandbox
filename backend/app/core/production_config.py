"""Production configuration validation — enforced at Settings load when ENVIRONMENT=production."""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from app.core.config import Settings

_LOCALHOST_HOSTS = frozenset({"localhost", "127.0.0.1", "::1", "0.0.0.0"})

_WEAK_SECRET_PREFIXES = (
    "change-me",
    "changeme",
    "change_me",
    "placeholder",
    "example",
    "your-",
    "test-",
    "re_change-me",
)

_WEAK_SECRET_EXACT = frozenset(
    {
        "sandbox",
        "postgres",
        "password",
        "admin",
        "secret",
        "12345678901234567890123456789012",
    }
)

_WEAK_DB_SUBSTRINGS = ("changeme", "change-me", "change_me")

_WEAK_DB_EXACT = frozenset(
    {
        "sandbox",
        "postgres",
        "password",
        "admin",
        "1234567890123456",
    }
)


def _normalized(value: str) -> str:
    return value.strip().lower()


def is_localhost_host(host: str | None) -> bool:
    if not host:
        return False
    lowered = host.lower()
    if lowered in _LOCALHOST_HOSTS:
        return True
    return lowered.endswith(".local")


def is_localhost_url(url: str) -> bool:
    parsed = urlparse(url.strip())
    return is_localhost_host(parsed.hostname)


def is_weak_secret(value: str) -> bool:
    """App/crypto secrets — expect high entropy and minimum length."""
    normalized = _normalized(value)
    if len(normalized) < 32:
        return True
    if normalized in _WEAK_SECRET_EXACT:
        return True
    return any(normalized.startswith(prefix) for prefix in _WEAK_SECRET_PREFIXES)


def is_placeholder_api_key(value: str, *, prefixes: tuple[str, ...]) -> bool:
    normalized = _normalized(value)
    if not normalized:
        return True
    return any(normalized.startswith(prefix) for prefix in prefixes)


def is_weak_database_password(password: str) -> bool:
    normalized = _normalized(password)
    if len(normalized) < 16:
        return True
    if normalized in _WEAK_DB_EXACT:
        return True
    return any(fragment in normalized for fragment in _WEAK_DB_SUBSTRINGS)


def collect_production_config_errors(settings: Settings) -> list[str]:
    errors: list[str] = []

    if settings.DEBUG:
        errors.append("Production requires DEBUG=false")

    if settings.LOG_LEVEL.strip().upper() == "DEBUG":
        errors.append("Production requires LOG_LEVEL other than DEBUG")

    if settings.SCAN_RUN_INLINE:
        errors.append("Production requires SCAN_RUN_INLINE=false (use Celery workers)")

    if settings.REPORT_RUN_INLINE:
        errors.append("Production requires REPORT_RUN_INLINE=false (use Celery workers)")

    if is_weak_secret(settings.SECRET_KEY):
        errors.append("Production requires a strong non-default SECRET_KEY (min 32 chars)")

    if is_weak_secret(settings.JWT_SECRET):
        errors.append("Production requires a strong non-default JWT_SECRET (min 32 chars)")

    if is_weak_database_password(settings.POSTGRES_PASSWORD):
        errors.append("Production requires a strong non-default POSTGRES_PASSWORD")

    if _normalized(settings.POSTGRES_USER) in {"postgres", "admin", "root"}:
        errors.append("Production requires a non-default POSTGRES_USER")

    if not settings.RESEND_API_KEY.strip():
        errors.append("Production requires RESEND_API_KEY for transactional email")
    elif is_placeholder_api_key(
        settings.RESEND_API_KEY,
        prefixes=("re_change-me", "re_test", "re_placeholder", "re_example"),
    ):
        errors.append("Production requires a non-placeholder RESEND_API_KEY")

    if not settings.BACKUP_ENCRYPTION_PASSPHRASE.strip():
        errors.append("Production requires BACKUP_ENCRYPTION_PASSPHRASE for encrypted backups")
    elif is_weak_secret(settings.BACKUP_ENCRYPTION_PASSPHRASE):
        errors.append("Production requires a strong non-default BACKUP_ENCRYPTION_PASSPHRASE")

    if settings.REPORT_STORAGE_BACKEND == "s3" and not settings.REPORT_S3_BUCKET.strip():
        errors.append("Production requires REPORT_S3_BUCKET when REPORT_STORAGE_BACKEND=s3")

    for origin in settings.cors_origins_list:
        if is_localhost_url(origin):
            errors.append(f"Production CORS_ORIGINS must not include localhost: {origin}")
            break
        if not origin.lower().startswith("https://"):
            errors.append(f"Production CORS_ORIGINS must use HTTPS: {origin}")
            break

    if is_localhost_url(settings.FRONTEND_URL):
        errors.append("Production FRONTEND_URL must not point to localhost")
    elif not settings.FRONTEND_URL.lower().startswith("https://"):
        errors.append("Production FRONTEND_URL must use HTTPS")

    if is_localhost_url(settings.PUBLIC_API_URL):
        errors.append("Production PUBLIC_API_URL must not point to localhost")
    elif not settings.PUBLIC_API_URL.lower().startswith("https://"):
        errors.append("Production PUBLIC_API_URL must use HTTPS")

    if settings.AI_ENABLED:
        if not settings.OPENAI_API_KEY.strip():
            errors.append(
                "Production requires OPENAI_API_KEY when AI_ENABLED=true "
                "(set AI_ENABLED=false for assessment-only deployments)"
            )
        elif settings.OPENAI_API_KEY.lower().startswith(("sk-change-me", "sk-test", "sk-placeholder")):
            errors.append("Production requires a non-placeholder OPENAI_API_KEY when AI_ENABLED=true")

    return errors


def validate_production_settings(settings: Settings) -> None:
    errors = collect_production_config_errors(settings)
    if errors:
        raise ValueError("; ".join(errors))
