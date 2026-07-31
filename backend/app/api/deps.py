from typing import Annotated, Callable
import uuid

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.permissions import Permission
from app.core.rbac import has_all_permissions, has_any_permission, has_permission
from app.core.security import decode_access_token
from app.members.enums import MemberStatus
from app.members.models import OrganizationMember
from app.members.repositories.member_repository import get_membership
from app.users.models import User
from app.organizations.repositories.organization_repository import get_organization_by_id
from app.users.repositories.user_repository import get_user_by_id


def get_current_user(
    db: Session = Depends(get_db),
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Authentication required")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired access token") from exc

    user = get_user_by_id(db, payload.user_id)
    if not user or not user.is_active:
        raise UnauthorizedError("Account is inactive or not found")

    return user


def get_organization_id_header(
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-ID")] = None,
) -> uuid.UUID | None:
    if not x_organization_id:
        return None
    try:
        return uuid.UUID(x_organization_id)
    except ValueError as exc:
        raise UnauthorizedError("Invalid X-Organization-ID header") from exc


def get_current_session_id_header(
    x_session_id: Annotated[str | None, Header(alias="X-Session-ID")] = None,
) -> uuid.UUID | None:
    if not x_session_id:
        return None
    try:
        return uuid.UUID(x_session_id)
    except ValueError as exc:
        raise UnauthorizedError("Invalid X-Session-ID header") from exc


def get_current_membership(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: uuid.UUID | None = Depends(get_organization_id_header),
) -> OrganizationMember:
    if organization_id is None:
        raise UnauthorizedError("X-Organization-ID header is required")

    if not get_organization_by_id(db, organization_id):
        raise NotFoundError("Organization")

    membership = get_membership(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    if not membership:
        raise ForbiddenError("You are not a member of this organization")

    if membership.status == MemberStatus.INVITED:
        raise ForbiddenError("You must accept the organization invitation first")
    if membership.status == MemberStatus.SUSPENDED:
        raise ForbiddenError("Your membership in this organization is suspended")

    return membership


def get_current_membership_any_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: uuid.UUID | None = Depends(get_organization_id_header),
) -> OrganizationMember:
    """Resolve membership without enforcing active status (e.g. invitation accept)."""
    if organization_id is None:
        raise UnauthorizedError("X-Organization-ID header is required")

    if not get_organization_by_id(db, organization_id):
        raise NotFoundError("Organization")

    membership = get_membership(
        db,
        organization_id=organization_id,
        user_id=current_user.id,
    )
    if not membership:
        raise ForbiddenError("You are not a member of this organization")

    return membership


def require_permission(permission: Permission) -> Callable:
    def dependency(
        membership: OrganizationMember = Depends(get_current_membership),
    ) -> OrganizationMember:
        if not has_permission(membership.role, permission):
            raise ForbiddenError(f"Missing permission: {permission.value}")
        return membership

    return dependency


def require_any_permission(*permissions: Permission) -> Callable:
    def dependency(
        membership: OrganizationMember = Depends(get_current_membership),
    ) -> OrganizationMember:
        if not has_any_permission(membership.role, *permissions):
            required = ", ".join(p.value for p in permissions)
            raise ForbiddenError(f"Missing one of required permissions: {required}")
        return membership

    return dependency


def require_all_permissions(*permissions: Permission) -> Callable:
    def dependency(
        membership: OrganizationMember = Depends(get_current_membership),
    ) -> OrganizationMember:
        if not has_all_permissions(membership.role, *permissions):
            required = ", ".join(p.value for p in permissions)
            raise ForbiddenError(f"Missing required permissions: {required}")
        return membership

    return dependency
