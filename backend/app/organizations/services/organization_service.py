import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.core.slug import slugify, unique_slug
from app.members.enums import MemberStatus, OrganizationRole
from app.members.models import OrganizationMember
from app.members.repositories.member_repository import add_organization_member
from app.users.models import User
from app.organizations.events import OrganizationAuditAction
from app.organizations.models import Organization
from app.organizations.repositories.organization_repository import (
    create_organization,
    deactivate_organization,
    get_organization_by_slug,
    update_organization,
)
from app.organizations.schemas import (
    CreateOrganizationRequest,
    OrganizationDetail,
    OrganizationSettings,
    OrganizationSummary,
    UpdateOrganizationRequest,
)
from app.organizations.settings_defaults import merge_organization_settings
from app.audit.service import record_audit_event


def to_organization_summary(membership: OrganizationMember) -> OrganizationSummary:
    org = membership.organization
    return OrganizationSummary(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        role=membership.role,
        membership_status=membership.status,
        is_active=org.is_active,
    )


def to_organization_detail(organization: Organization) -> OrganizationDetail:
    merged_settings = merge_organization_settings(getattr(organization, "settings", None) or {})
    return OrganizationDetail(
        id=str(organization.id),
        name=organization.name,
        slug=organization.slug,
        description=organization.description,
        industry=organization.industry,
        website=organization.website,
        logo_url=organization.logo_url,
        country=organization.country,
        timezone=organization.timezone,
        settings=OrganizationSettings.model_validate(merged_settings),
        created_by=str(organization.created_by) if organization.created_by else None,
        is_active=organization.is_active,
    )


def list_user_organizations(db: Session, user: User) -> list[OrganizationSummary]:
    from app.members.repositories.member_repository import list_memberships_for_user

    memberships = list_memberships_for_user(db, user.id)
    return [to_organization_summary(membership) for membership in memberships]


def create_user_organization(
    db: Session,
    user: User,
    *,
    body: CreateOrganizationRequest,
) -> OrganizationDetail:
    slug = slugify(body.slug or body.name)
    if get_organization_by_slug(db, slug):
        slug = unique_slug(body.name, suffix=uuid.uuid4())

    organization = create_organization(
        db,
        name=body.name,
        slug=slug,
        description=body.description,
        industry=body.industry,
        website=body.website,
        logo_url=body.logo_url,
        country=body.country,
        timezone=body.timezone,
        created_by=user.id,
    )
    add_organization_member(
        db,
        organization_id=organization.id,
        user_id=user.id,
        role=OrganizationRole.OWNER,
        status=MemberStatus.ACTIVE,
        joined_at=datetime.now(UTC),
    )
    record_audit_event(
        db,
        action=OrganizationAuditAction.CREATE,
        user_id=user.id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
        details={"name": organization.name, "slug": organization.slug},
    )
    db.commit()
    db.refresh(organization)
    return to_organization_detail(organization)


def get_current_organization(
    db: Session,
    membership: OrganizationMember,
) -> OrganizationDetail:
    organization = membership.organization
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")
    return to_organization_detail(organization)


def update_current_organization(
    db: Session,
    membership: OrganizationMember,
    *,
    body: UpdateOrganizationRequest,
) -> OrganizationDetail:
    organization = membership.organization
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")
    if body.model_dump(exclude_unset=True) == {}:
        raise ValidationAppError("At least one field must be provided")

    settings_payload = None
    if body.settings is not None:
        current = merge_organization_settings(organization.settings)
        if body.settings.language is not None:
            current["language"] = body.settings.language
        if body.settings.notifications is not None:
            current["notifications"].update(
                body.settings.notifications.model_dump(exclude_none=True)
            )
        if body.settings.security is not None:
            current["security"].update(body.settings.security.model_dump(exclude_none=True))
        settings_payload = current

    update_organization(
        db,
        organization,
        name=body.name,
        description=body.description,
        industry=body.industry,
        website=body.website,
        logo_url=body.logo_url,
        country=body.country,
        timezone=body.timezone,
        settings=settings_payload,
    )
    record_audit_event(
        db,
        action=OrganizationAuditAction.UPDATE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
        details=body.model_dump(exclude_unset=True),
    )
    db.commit()
    db.refresh(organization)
    return to_organization_detail(organization)


def archive_current_organization(db: Session, membership: OrganizationMember) -> OrganizationDetail:
    organization = membership.organization
    if membership.role != OrganizationRole.OWNER:
        raise ForbiddenError("Only the organization owner can archive the organization")
    if not organization.is_active:
        raise ValidationAppError("Organization is already archived")

    update_organization(db, organization, is_active=False)
    record_audit_event(
        db,
        action=OrganizationAuditAction.ARCHIVE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
    )
    db.commit()
    db.refresh(organization)
    return to_organization_detail(organization)


def delete_current_organization(db: Session, membership: OrganizationMember) -> None:
    organization = membership.organization
    if membership.role != OrganizationRole.OWNER:
        raise ForbiddenError("Only the organization owner can delete the organization")
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")

    deactivate_organization(db, organization)
    record_audit_event(
        db,
        action=OrganizationAuditAction.DELETE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
    )
    db.commit()
