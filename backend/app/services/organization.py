import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.slug import slugify, unique_slug
from app.models.organization import Organization
from app.models.organization_member import OrganizationMember, OrganizationRole
from app.models.user import User
from app.repositories.organization import (
    add_organization_member,
    create_organization,
    deactivate_organization,
    get_membership,
    get_organization_by_slug,
    get_organization_member_by_id,
    list_memberships_for_user,
    list_organization_members,
    remove_organization_member,
    update_member_role,
    update_organization,
)
from app.repositories.user import get_user_by_email
from app.schemas.organization import (
    CreateOrganizationRequest,
    InviteMemberRequest,
    MemberSummary,
    OrganizationDetail,
    OrganizationSummary,
    TransferOwnershipRequest,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)
from app.services.audit import AuditAction, record_audit_event


def _to_organization_summary(membership: OrganizationMember) -> OrganizationSummary:
    org = membership.organization
    return OrganizationSummary(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        role=membership.role,
        is_active=org.is_active,
    )


def _to_organization_detail(organization: Organization) -> OrganizationDetail:
    return OrganizationDetail(
        id=str(organization.id),
        name=organization.name,
        slug=organization.slug,
        description=organization.description,
        is_active=organization.is_active,
    )


def _to_member_summary(membership: OrganizationMember) -> MemberSummary:
    user = membership.user
    return MemberSummary(
        membership_id=str(membership.id),
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=membership.role,
    )


def list_user_organizations(db: Session, user: User) -> list[OrganizationSummary]:
    memberships = list_memberships_for_user(db, user.id)
    return [_to_organization_summary(membership) for membership in memberships]


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
    )
    add_organization_member(
        db,
        organization_id=organization.id,
        user_id=user.id,
        role=OrganizationRole.OWNER,
    )
    record_audit_event(
        db,
        action=AuditAction.ORG_CREATE,
        user_id=user.id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
        details={"name": organization.name, "slug": organization.slug},
    )
    db.commit()
    db.refresh(organization)
    return _to_organization_detail(organization)


def get_current_organization(
    db: Session,
    membership: OrganizationMember,
) -> OrganizationDetail:
    organization = membership.organization
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")
    return _to_organization_detail(organization)


def update_current_organization(
    db: Session,
    membership: OrganizationMember,
    *,
    body: UpdateOrganizationRequest,
) -> OrganizationDetail:
    organization = membership.organization
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")
    if body.name is None and body.description is None:
        raise ValidationAppError("At least one field must be provided")

    update_organization(
        db,
        organization,
        name=body.name,
        description=body.description,
    )
    record_audit_event(
        db,
        action=AuditAction.ORG_UPDATE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
        details={"name": body.name, "description": body.description},
    )
    db.commit()
    db.refresh(organization)
    return _to_organization_detail(organization)


def delete_current_organization(db: Session, membership: OrganizationMember) -> None:
    organization = membership.organization
    if membership.role != OrganizationRole.OWNER:
        raise ForbiddenError("Only the organization owner can delete the organization")
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")

    deactivate_organization(db, organization)
    record_audit_event(
        db,
        action=AuditAction.ORG_DELETE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
    )
    db.commit()


def list_current_organization_members(
    db: Session,
    membership: OrganizationMember,
) -> list[MemberSummary]:
    members = list_organization_members(db, membership.organization_id)
    return [_to_member_summary(member) for member in members]


def invite_member(
    db: Session,
    membership: OrganizationMember,
    *,
    body: InviteMemberRequest,
) -> MemberSummary:
    organization = membership.organization
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")

    user = get_user_by_email(db, str(body.email))
    if not user:
        raise NotFoundError("User", "No account exists with that email address")
    if not user.is_active:
        raise ValidationAppError("Cannot invite an inactive user")

    existing = next(
        (member for member in list_organization_members(db, organization.id) if member.user_id == user.id),
        None,
    )
    if existing:
        raise ConflictError("User is already a member of this organization")

    created = add_organization_member(
        db,
        organization_id=organization.id,
        user_id=user.id,
        role=body.role,
    )
    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_INVITE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization_member",
        resource_id=created.id,
        details={
            "invited_user_id": str(user.id),
            "invited_email": user.email,
            "role": body.role.value,
        },
    )
    db.commit()
    db.refresh(created)
    created = get_organization_member_by_id(
        db,
        membership_id=created.id,
        organization_id=organization.id,
    )
    return _to_member_summary(created)


def update_member(
    db: Session,
    membership: OrganizationMember,
    *,
    target_membership_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
) -> MemberSummary:
    target = get_organization_member_by_id(
        db,
        membership_id=target_membership_id,
        organization_id=membership.organization_id,
    )
    if not target:
        raise NotFoundError("Member")

    if target.role == OrganizationRole.OWNER:
        raise ForbiddenError("Cannot change the owner's role directly")

    if membership.user_id == target.user_id and body.role != membership.role:
        raise ForbiddenError("You cannot change your own role")

    updated = update_member_role(db, target, role=body.role)
    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization_member",
        resource_id=target.id,
        details={
            "target_user_id": str(target.user_id),
            "role": body.role.value,
        },
    )
    db.commit()
    db.refresh(updated)
    return _to_member_summary(updated)


def remove_member(
    db: Session,
    membership: OrganizationMember,
    *,
    target_membership_id: uuid.UUID,
) -> None:
    target = get_organization_member_by_id(
        db,
        membership_id=target_membership_id,
        organization_id=membership.organization_id,
    )
    if not target:
        raise NotFoundError("Member")

    if target.role == OrganizationRole.OWNER:
        raise ForbiddenError("Cannot remove the organization owner")

    if membership.user_id == target.user_id:
        raise ForbiddenError("You cannot remove yourself from the organization")

    remove_organization_member(db, target)
    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_REMOVE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization_member",
        resource_id=target.id,
        details={"removed_user_id": str(target.user_id)},
    )
    db.commit()


def transfer_organization_ownership(
    db: Session,
    membership: OrganizationMember,
    *,
    body: TransferOwnershipRequest,
) -> MemberSummary:
    if membership.role != OrganizationRole.OWNER:
        raise ForbiddenError("Only the organization owner can transfer ownership")

    try:
        new_owner_user_id = uuid.UUID(body.new_owner_user_id)
    except ValueError as exc:
        raise ValidationAppError("Invalid new_owner_user_id") from exc

    if new_owner_user_id == membership.user_id:
        raise ValidationAppError("You are already the organization owner")

    target = get_membership(
        db,
        organization_id=membership.organization_id,
        user_id=new_owner_user_id,
    )
    if not target:
        raise NotFoundError("Member", "New owner must already be a member of the organization")

    update_member_role(db, membership, role=OrganizationRole.ADMIN)
    update_member_role(db, target, role=OrganizationRole.OWNER)
    record_audit_event(
        db,
        action=AuditAction.ORG_OWNERSHIP_TRANSFER,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization",
        resource_id=membership.organization_id,
        details={"new_owner_user_id": str(target.user_id)},
    )
    db.commit()
    db.refresh(target)
    return _to_member_summary(target)
