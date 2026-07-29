import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.core.security import hash_token
from app.models.organization_member import OrganizationMember
from app.models.password_reset_token import PasswordResetToken
from app.models.user import User


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(
    db: Session,
    *,
    email: str,
    hashed_password: str,
    first_name: str,
    last_name: str,
) -> User:
    user = User(
        email=email,
        hashed_password=hashed_password,
        first_name=first_name,
        last_name=last_name,
    )
    db.add(user)
    db.flush()
    return user


def update_user_password(db: Session, user: User, hashed_password: str) -> None:
    user.hashed_password = hashed_password
    db.add(user)


def get_primary_membership(db: Session, user_id: uuid.UUID) -> OrganizationMember | None:
    return (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.organization))
        .filter(OrganizationMember.user_id == user_id)
        .order_by(OrganizationMember.created_at.asc())
        .first()
    )


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
