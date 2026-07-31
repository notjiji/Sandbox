import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.auth.models import RefreshToken
from app.core.security import hash_token


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
        revoked=False,
    )
    db.add(record)
    db.flush()
    return record


def revoke_refresh_token(db: Session, record: RefreshToken, replaced_by_id: uuid.UUID | None = None) -> None:
    record.revoked = True
    record.revoked_at = datetime.now(UTC)
    if replaced_by_id:
        record.replaced_by_id = replaced_by_id
    db.add(record)


def revoke_all_user_refresh_tokens(db: Session, user_id: uuid.UUID) -> None:
    now = datetime.now(UTC)
    records = (
        db.query(RefreshToken)
        .filter(RefreshToken.user_id == user_id, RefreshToken.revoked.is_(False))
        .all()
    )
    for record in records:
        record.revoked = True
        record.revoked_at = now
        db.add(record)


def is_refresh_token_valid(record: RefreshToken) -> bool:
    if record.revoked:
        return False
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at > datetime.now(UTC)


def list_active_sessions_for_user(db: Session, user_id: uuid.UUID) -> list[RefreshToken]:
    now = datetime.now(UTC)
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked.is_(False),
            RefreshToken.expires_at > now,
        )
        .order_by(RefreshToken.created_at.desc())
        .all()
    )


def get_user_session_by_id(
    db: Session,
    *,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
) -> RefreshToken | None:
    return (
        db.query(RefreshToken)
        .filter(
            RefreshToken.id == session_id,
            RefreshToken.user_id == user_id,
        )
        .first()
    )


def revoke_all_user_sessions_except(
    db: Session,
    user_id: uuid.UUID,
    *,
    except_session_id: uuid.UUID,
) -> int:
    now = datetime.now(UTC)
    records = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == user_id,
            RefreshToken.id != except_session_id,
            RefreshToken.revoked.is_(False),
        )
        .all()
    )
    for record in records:
        record.revoked = True
        record.revoked_at = now
        db.add(record)
    return len(records)
