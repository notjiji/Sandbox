import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.organizations.models import Organization
from app.organizations.settings_defaults import merge_organization_settings


def get_active_organization_by_id(
    db: Session,
    organization_id: uuid.UUID,
) -> Organization | None:
    organization = get_organization_by_id(db, organization_id)
    if organization is None or not organization.is_active or organization.deleted_at is not None:
        return None
    return organization


def get_restorable_organization_by_id(
    db: Session,
    organization_id: uuid.UUID,
) -> Organization | None:
    organization = get_organization_by_id(db, organization_id)
    if organization is None or organization.deleted_at is not None:
        return None
    return organization


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
    industry: str | None = None,
    website: str | None = None,
    logo_url: str | None = None,
    country: str | None = None,
    timezone: str | None = None,
    created_by: uuid.UUID | None = None,
) -> Organization:
    organization = Organization(
        name=name,
        slug=slug,
        description=description,
        industry=industry,
        website=website,
        logo_url=logo_url,
        country=country,
        timezone=timezone,
        created_by=created_by,
        is_active=True,
    )
    db.add(organization)
    db.flush()
    return organization


def update_organization(
    db: Session,
    organization: Organization,
    *,
    name: str | None = None,
    description: str | None = None,
    industry: str | None = None,
    website: str | None = None,
    logo_url: str | None = None,
    country: str | None = None,
    timezone: str | None = None,
    settings: dict | None = None,
    is_active: bool | None = None,
) -> Organization:
    if name is not None:
        organization.name = name
    if description is not None:
        organization.description = description
    if industry is not None:
        organization.industry = industry
    if website is not None:
        organization.website = website
    if logo_url is not None:
        organization.logo_url = logo_url
    if country is not None:
        organization.country = country
    if timezone is not None:
        organization.timezone = timezone
    if settings is not None:
        organization.settings = settings
    if is_active is not None:
        organization.is_active = is_active
    db.add(organization)
    db.flush()
    return organization


def deactivate_organization(db: Session, organization: Organization) -> None:
    organization.is_active = False
    db.add(organization)


def soft_delete_organization(
    db: Session,
    organization: Organization,
    *,
    deleted_at: datetime,
) -> None:
    organization.is_active = False
    organization.deleted_at = deleted_at
    db.add(organization)


def restore_organization(db: Session, organization: Organization) -> None:
    organization.is_active = True
    organization.deleted_at = None
    db.add(organization)
