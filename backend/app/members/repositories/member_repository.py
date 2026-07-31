import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.members.enums import MemberStatus, OrganizationRole
from app.members.models import OrganizationMember


def get_membership(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
) -> OrganizationMember | None:
    return (
        db.query(OrganizationMember)
        .options(
            joinedload(OrganizationMember.organization),
            joinedload(OrganizationMember.user),
        )
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.user_id == user_id,
        )
        .first()
    )


def list_memberships_for_user(db: Session, user_id: uuid.UUID) -> list[OrganizationMember]:
    return (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.organization))
        .filter(OrganizationMember.user_id == user_id)
        .order_by(OrganizationMember.created_at.asc())
        .all()
    )


def list_organization_members(db: Session, organization_id: uuid.UUID) -> list[OrganizationMember]:
    return (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.user))
        .filter(OrganizationMember.organization_id == organization_id)
        .order_by(OrganizationMember.created_at.asc())
        .all()
    )


def get_organization_member_by_id(
    db: Session,
    *,
    membership_id: uuid.UUID,
    organization_id: uuid.UUID,
) -> OrganizationMember | None:
    return (
        db.query(OrganizationMember)
        .options(joinedload(OrganizationMember.user))
        .filter(
            OrganizationMember.id == membership_id,
            OrganizationMember.organization_id == organization_id,
        )
        .first()
    )


def get_organization_owner(db: Session, organization_id: uuid.UUID) -> OrganizationMember | None:
    return (
        db.query(OrganizationMember)
        .filter(
            OrganizationMember.organization_id == organization_id,
            OrganizationMember.role == OrganizationRole.OWNER,
        )
        .first()
    )


def add_organization_member(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role: OrganizationRole,
    status: MemberStatus = MemberStatus.ACTIVE,
    joined_at: datetime | None = None,
) -> OrganizationMember:
    membership = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
        status=status,
        joined_at=joined_at,
    )
    db.add(membership)
    db.flush()
    return membership


def update_member_role(
    db: Session,
    membership: OrganizationMember,
    *,
    role: OrganizationRole | None = None,
    status: MemberStatus | None = None,
) -> OrganizationMember:
    if role is not None:
        membership.role = role
    if status is not None:
        membership.status = status
        if status == MemberStatus.ACTIVE and membership.joined_at is None:
            membership.joined_at = datetime.now(UTC)
    db.add(membership)
    db.flush()
    return membership


def remove_organization_member(db: Session, membership: OrganizationMember) -> None:
    db.delete(membership)


def list_organization_roles() -> list[OrganizationRole]:
    return list(OrganizationRole)
