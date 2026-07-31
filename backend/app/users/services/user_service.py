from sqlalchemy.orm import Session

from app.audit.service import record_auth_event
from app.users.events import UserAuditAction
from app.users.models import User
from app.users.repository import get_primary_membership, update_user_profile
from app.users.schemas import UpdateUserProfileRequest, UserProfileResponse


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


def update_profile(
    db: Session,
    user: User,
    *,
    body: UpdateUserProfileRequest,
) -> UserProfileResponse:
    update_user_profile(
        db,
        user,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    record_auth_event(
        db,
        action=UserAuditAction.PROFILE_UPDATE,
        user_id=user.id,
        resource_type="user",
        resource_id=user.id,
        details={
            "first_name": body.first_name,
            "last_name": body.last_name,
        },
    )
    db.commit()
    db.refresh(user)
    return get_user_profile(db, user)
