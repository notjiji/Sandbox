import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

ACCESS_TOKEN_TYPE = "access"


@dataclass(frozen=True)
class AccessTokenContext:
    user_id: uuid.UUID
    email: str
    organization_id: str | None
    role: str | None


@dataclass(frozen=True)
class AccessTokenPayload(AccessTokenContext):
    pass


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def hash_token(token: str) -> str:
    import hashlib

    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_opaque_token() -> str:
    import secrets

    return secrets.token_urlsafe(48)


def create_access_token(context: AccessTokenContext) -> tuple[str, int]:
    settings = get_settings()
    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_SECONDS
    expire = datetime.now(UTC) + timedelta(seconds=expires_in)
    payload = {
        "sub": str(context.user_id),
        "email": context.email,
        "organization_id": context.organization_id or "",
        "role": context.role or "",
        "type": ACCESS_TOKEN_TYPE,
        "exp": expire,
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token, expires_in


def decode_access_token(token: str) -> AccessTokenPayload:
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise ValueError("Invalid access token") from exc

    if payload.get("type") != ACCESS_TOKEN_TYPE:
        raise ValueError("Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise ValueError("Invalid token subject")

    organization_id = payload.get("organization_id") or None
    role = payload.get("role") or None

    return AccessTokenPayload(
        user_id=uuid.UUID(user_id),
        email=payload.get("email", ""),
        organization_id=organization_id if organization_id else None,
        role=role if role else None,
    )


def get_refresh_token_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)


def get_password_reset_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(UTC) + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
