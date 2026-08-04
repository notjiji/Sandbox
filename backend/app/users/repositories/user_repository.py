import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.members.enums import MemberStatus
from app.members.models import OrganizationMember
from app.users.models import User


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


def mark_user_verified(db: Session, user: User) -> None:
    user.is_verified = True
    db.add(user)


def update_last_login(db: Session, user: User) -> None:
    user.last_login = datetime.now(UTC)
    db.add(user)


def update_user_profile(
    db: Session,
    user: User,
    *,
    first_name: str,
    last_name: str,
) -> User:
    user.first_name = first_name
    user.last_name = last_name
    db.add(user)
    db.flush()
    return user


def get_primary_membership(db: Session, user_id: uuid.UUID) -> OrganizationMember | None:
    return (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.organization))
        .filter(
            OrganizationMember.user_id == user_id,
            OrganizationMember.status == MemberStatus.ACTIVE,
        )
        .order_by(OrganizationMember.created_at.asc())
        .first()
    )
