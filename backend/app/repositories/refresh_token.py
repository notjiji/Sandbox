import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.security import hash_token
from app.models.refresh_token import RefreshToken


def get_refresh_token_by_hash(db: Session, token: str) -> RefreshToken | None:
    token_hash = hash_token(token)
    return db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()


def create_refresh_token_record(
    db: Session,
    *,
    user_id: uuid.UUID,
    token: str,
    expires_at: datetime,
) -> RefreshToken:
    record = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(token),
        expires_at=expires_at,
    )
    db.add(record)
    db.flush()
    return record


def revoke_refresh_token(db: Session, record: RefreshToken, replaced_by_id: uuid.UUID | None = None) -> None:
    record.revoked_at = datetime.now(UTC)
    if replaced_by_id:
        record.replaced_by_id = replaced_by_id
    db.add(record)


def is_refresh_token_valid(record: RefreshToken) -> bool:
    if record.revoked_at is not None:
        return False
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > datetime.now(UTC)
