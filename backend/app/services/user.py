from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories.user import get_primary_membership
from app.schemas.user import UserProfileResponse


def get_user_profile(db: Session, user: User) -> UserProfileResponse:
    membership = get_primary_membership(db, user.id)
    organization_name = membership.organization.name if membership else None
    role = membership.role.value if membership else None

    return UserProfileResponse(
        id=str(user.id),
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_verified=user.is_verified,
        role=role,
        organization=organization_name,
    )
