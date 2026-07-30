import uuid

from sqlalchemy.orm import Session, joinedload

from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole


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


def get_organization_by_id(db: Session, organization_id: uuid.UUID) -> Organization | None:
    return db.query(Organization).filter(Organization.id == organization_id).first()


def get_organization_by_slug(db: Session, slug: str) -> Organization | None:
    return db.query(Organization).filter(Organization.slug == slug).first()


def create_organization(
    db: Session,
    *,
    name: str,
    slug: str,
    description: str | None = None,
) -> Organization:
    organization = Organization(
        name=name,
        slug=slug,
        description=description,
        is_active=True,
    )
    db.add(organization)
    db.flush()
    return organization


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


def update_organization(
    db: Session,
    organization: Organization,
    *,
    name: str | None = None,
    description: str | None = None,
) -> Organization:
    if name is not None:
        organization.name = name
    if description is not None:
        organization.description = description
    db.add(organization)
    db.flush()
    return organization


def deactivate_organization(db: Session, organization: Organization) -> None:
    organization.is_active = False
    db.add(organization)


def add_organization_member(
    db: Session,
    *,
    organization_id: uuid.UUID,
    user_id: uuid.UUID,
    role: OrganizationRole,
) -> OrganizationMember:
    membership = OrganizationMember(
        organization_id=organization_id,
        user_id=user_id,
        role=role,
    )
    db.add(membership)
    db.flush()
    return membership


def update_member_role(
    db: Session,
    membership: OrganizationMember,
    *,
    role: OrganizationRole,
) -> OrganizationMember:
    membership.role = role
    db.add(membership)
    db.flush()
    return membership


def remove_organization_member(db: Session, membership: OrganizationMember) -> None:
    db.delete(membership)


def list_organization_roles() -> list[OrganizationRole]:
    return list(OrganizationRole)
