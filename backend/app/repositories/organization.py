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


def list_organization_roles() -> list[OrganizationRole]:
    return list(OrganizationRole)
