import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.auth.models import PasswordResetToken
from app.core.security import hash_token


def create_password_reset_token(
    db: Session,
    *,
    user_id: uuid.UUID,
    token: str,
    expires_at: datetime,
) -> PasswordResetToken:
    record = PasswordResetToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
        revoked=False,
    )
    db.add(record)
    db.flush()
    return record


def get_password_reset_token(db: Session, token: str) -> PasswordResetToken | None:
    token_hash = hash_token(token)
    return (
        db.query(PasswordResetToken)
        .options(joinedload(PasswordResetToken.user))
        .filter(PasswordResetToken.token_hash == token_hash)
        .first()
    )


def mark_password_reset_token_used(db: Session, record: PasswordResetToken) -> None:
    record.revoked = True
    record.used_at = datetime.now(UTC)
    db.add(record)


def is_password_reset_token_valid(record: PasswordResetToken) -> bool:
    if record.revoked:
        return False
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > datetime.now(UTC)
