import uuid

from sqlalchemy.orm import Session

from app.core.security import AccessTokenContext
from app.models.organization_member import OrganizationMember
from app.models.user import User
from app.repositories.user import get_primary_membership


def build_access_token_context(db: Session, user: User) -> AccessTokenContext:
    membership = get_primary_membership(db, user.id)
    return AccessTokenContext(
        user_id=user.id,
        email=user.email,
        organization_id=_membership_organization_id(membership),
        role=_membership_role(membership),
    )


def _membership_organization_id(membership: OrganizationMember | None) -> str | None:
    if not membership:
        return None
    return str(membership.organization_id)


def _membership_role(membership: OrganizationMember | None) -> str | None:
    if not membership:
        return None
    return membership.role.value
