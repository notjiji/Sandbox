from dataclasses import dataclass

from app.core.config import get_settings
from app.core.redis import get_redis_client


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _failure_key(email: str) -> str:
    return f"login_failures:{_normalize_email(email)}"


def _lock_key(email: str) -> str:
    return f"login_locked:{_normalize_email(email)}"


@dataclass(frozen=True)
class LockoutStatus:
    locked: bool
    retry_after_seconds: int | None = None
    newly_locked: bool = False
    failed_attempts: int = 0


def is_account_locked(email: str) -> bool:
    redis = get_redis_client()
    return bool(redis.exists(_lock_key(email)))


def get_lockout_remaining_seconds(email: str) -> int | None:
    redis = get_redis_client()
    ttl = redis.ttl(_lock_key(email))
    if ttl is None or ttl < 0:
        return None
    return ttl


def clear_login_lockout(email: str) -> None:
    redis = get_redis_client()
    redis.delete(_failure_key(email), _lock_key(email))


def record_failed_login(email: str) -> LockoutStatus:
    settings = get_settings()
    redis = get_redis_client()
    lock_key = _lock_key(email)

    if redis.exists(lock_key):
        return LockoutStatus(
            locked=True,
            retry_after_seconds=get_lockout_remaining_seconds(email),
        )

    failure_key = _failure_key(email)
    failed_attempts = int(redis.incr(failure_key))
    if failed_attempts == 1:
        redis.expire(failure_key, settings.ACCOUNT_LOCKOUT_WINDOW_SECONDS)

    if failed_attempts >= settings.ACCOUNT_LOCKOUT_MAX_ATTEMPTS:
        redis.setex(lock_key, settings.ACCOUNT_LOCKOUT_DURATION_SECONDS, "1")
        redis.delete(failure_key)
        return LockoutStatus(
            locked=True,
            retry_after_seconds=settings.ACCOUNT_LOCKOUT_DURATION_SECONDS,
            newly_locked=True,
            failed_attempts=failed_attempts,
        )

    return LockoutStatus(locked=False, failed_attempts=failed_attempts)


def get_lockout_status(email: str) -> LockoutStatus:
    if not is_account_locked(email):
        return LockoutStatus(locked=False)
    return LockoutStatus(
        locked=True,
        retry_after_seconds=get_lockout_remaining_seconds(email),
    )
