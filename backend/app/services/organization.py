import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.security import (
    generate_opaque_token,
    get_organization_invite_expiry,
    hash_token,
)
from app.core.slug import slugify, unique_slug
from app.models.organization import Organization
from app.models.organization_member import MemberStatus, OrganizationMember, OrganizationRole
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
from app.repositories.organization_invite import (
    create_organization_invite,
    get_invite_by_id,
    get_invite_by_token_hash,
    get_pending_invite_by_email,
    is_invite_valid,
    list_pending_invites_for_organization,
    mark_invite_accepted,
    refresh_organization_invite,
    revoke_organization_invite,
)
from app.repositories.user import get_user_by_email
from app.schemas.auth import normalize_email
from app.schemas.organization import (
    CreateOrganizationRequest,
    InviteMemberRequest,
    InvitePreview,
    InviteResult,
    MemberSummary,
    OrganizationDetail,
    OrganizationSummary,
    PendingInviteSummary,
    TransferOwnershipRequest,
    UpdateMemberRoleRequest,
    UpdateOrganizationRequest,
)
from app.services.audit import AuditAction, record_audit_event
from app.services.email import send_organization_invite_email


def _to_organization_summary(membership: OrganizationMember) -> OrganizationSummary:
    org = membership.organization
    return OrganizationSummary(
        id=str(org.id),
        name=org.name,
        slug=org.slug,
        role=membership.role,
        membership_status=membership.status,
        is_active=org.is_active,
    )


def _to_organization_detail(organization: Organization) -> OrganizationDetail:
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
        created_by=str(organization.created_by) if organization.created_by else None,
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
        status=membership.status,
        joined_at=membership.joined_at,
    )


def _to_pending_invite_summary(invite) -> PendingInviteSummary:
    return PendingInviteSummary(
        invite_id=str(invite.id),
        email=invite.email,
        role=invite.role,
        status=invite.status.value,
        invited_at=invite.created_at,
        expires_at=invite.expires_at,
        membership_id=str(invite.membership_id) if invite.membership_id else None,
    )


def _inviter_display_name(user: User) -> str:
    return f"{user.first_name} {user.last_name}".strip() or user.email


def _build_invite_link(token: str) -> str:
    settings = get_settings()
    return f"{settings.FRONTEND_URL.rstrip('/')}/accept-invite?token={token}"


def _send_invite_email(
    *,
    to_email: str,
    organization: Organization,
    role: OrganizationRole,
    token: str,
    inviter: User,
) -> None:
    send_organization_invite_email(
        to_email=to_email,
        organization_name=organization.name,
        role=role.value.replace("_", " "),
        invite_link=_build_invite_link(token),
        inviter_name=_inviter_display_name(inviter),
    )


def _activate_membership(db: Session, membership: OrganizationMember) -> OrganizationMember:
    return update_member_role(
        db,
        membership,
        status=MemberStatus.ACTIVE,
    )


def _finalize_invite_acceptance(
    db: Session,
    *,
    invite,
    user: User,
    membership: OrganizationMember,
) -> OrganizationMember:
    if membership.status != MemberStatus.ACTIVE:
        _activate_membership(db, membership)
    if invite.status.value != "accepted":
        mark_invite_accepted(db, invite)
    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_ACCEPT,
        user_id=user.id,
        organization_id=invite.organization_id,
        resource_type="organization_member",
        resource_id=membership.id,
        details={"invite_id": str(invite.id)},
    )
    return membership


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
    if body.model_dump(exclude_none=True) == {}:
        raise ValidationAppError("At least one field must be provided")

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
    )
    record_audit_event(
        db,
        action=AuditAction.ORG_UPDATE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization",
        resource_id=organization.id,
        details=body.model_dump(exclude_none=True),
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


def list_current_pending_invites(
    db: Session,
    membership: OrganizationMember,
) -> list[PendingInviteSummary]:
    invites = list_pending_invites_for_organization(db, organization_id=membership.organization_id)
    return [_to_pending_invite_summary(invite) for invite in invites]


def invite_member(
    db: Session,
    membership: OrganizationMember,
    *,
    body: InviteMemberRequest,
) -> InviteResult:
    organization = membership.organization
    if not organization.is_active:
        raise NotFoundError("Organization", "Organization is inactive")

    email = normalize_email(str(body.email))
    inviter = membership.user

    user = get_user_by_email(db, email)
    if user and not user.is_active:
        raise ValidationAppError("Cannot invite an inactive user")

    if user:
        existing = get_membership(
            db,
            organization_id=organization.id,
            user_id=user.id,
        )
        if existing and existing.status == MemberStatus.ACTIVE:
            raise ConflictError("User is already a member of this organization")
        if existing and existing.status == MemberStatus.SUSPENDED:
            raise ConflictError("User is suspended in this organization")

    pending_invite = get_pending_invite_by_email(
        db,
        organization_id=organization.id,
        email=email,
    )

    token = generate_opaque_token()
    token_hash = hash_token(token)
    expires_at = get_organization_invite_expiry()
    created_membership = None

    if user:
        if existing := get_membership(db, organization_id=organization.id, user_id=user.id):
            if existing.status == MemberStatus.INVITED:
                update_member_role(db, existing, role=body.role, status=MemberStatus.INVITED)
                created_membership = existing
            else:
                raise ConflictError("User is already a member of this organization")
        else:
            created_membership = add_organization_member(
                db,
                organization_id=organization.id,
                user_id=user.id,
                role=body.role,
                status=MemberStatus.INVITED,
            )

    if pending_invite:
        invite = refresh_organization_invite(
            db,
            pending_invite,
            token_hash=token_hash,
            expires_at=expires_at,
            role=body.role,
            membership_id=created_membership.id if created_membership else pending_invite.membership_id,
        )
    else:
        invite = create_organization_invite(
            db,
            organization_id=organization.id,
            email=email,
            role=body.role,
            token_hash=token_hash,
            invited_by=membership.user_id,
            expires_at=expires_at,
            membership_id=created_membership.id if created_membership else None,
        )

    _send_invite_email(
        to_email=email,
        organization=organization,
        role=body.role,
        token=token,
        inviter=inviter,
    )
    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_INVITE,
        user_id=membership.user_id,
        organization_id=organization.id,
        resource_type="organization_invite",
        resource_id=invite.id,
        details={
            "invited_email": email,
            "role": body.role.value,
            "user_exists": user is not None,
        },
    )
    db.commit()
    db.refresh(invite)
    return InviteResult(
        invite_id=str(invite.id),
        email=email,
        role=invite.role,
        status=invite.status.value,
        user_exists=user is not None,
        membership_id=str(created_membership.id) if created_membership else None,
    )


def get_invite_preview(db: Session, *, token: str) -> InvitePreview:
    invite = get_invite_by_token_hash(db, token_hash=hash_token(token))
    if not invite or not is_invite_valid(invite):
        raise NotFoundError("Invitation", "Invitation is invalid or has expired")

    organization = invite.organization
    inviter = invite.inviter
    user = get_user_by_email(db, invite.email)

    return InvitePreview(
        organization_id=str(organization.id),
        organization_name=organization.name,
        organization_slug=organization.slug,
        email=invite.email,
        role=invite.role,
        inviter_name=_inviter_display_name(inviter),
        expires_at=invite.expires_at,
        user_exists=user is not None,
    )


def accept_invite_by_token(db: Session, *, user: User, token: str) -> OrganizationSummary:
    invite = get_invite_by_token_hash(db, token_hash=hash_token(token))
    if not invite or not is_invite_valid(invite):
        raise NotFoundError("Invitation", "Invitation is invalid or has expired")

    if normalize_email(user.email) != invite.email:
        raise ForbiddenError("This invitation was sent to a different email address")

    if invite.membership_id:
        membership = get_organization_member_by_id(
            db,
            membership_id=invite.membership_id,
            organization_id=invite.organization_id,
        )
        if not membership:
            raise NotFoundError("Member")
    else:
        existing = get_membership(
            db,
            organization_id=invite.organization_id,
            user_id=user.id,
        )
        if existing:
            membership = existing
        else:
            membership = add_organization_member(
                db,
                organization_id=invite.organization_id,
                user_id=user.id,
                role=invite.role,
                status=MemberStatus.INVITED,
            )

    if membership.status == MemberStatus.ACTIVE:
        mark_invite_accepted(db, invite)
        db.commit()
        membership = get_membership(
            db,
            organization_id=invite.organization_id,
            user_id=user.id,
        )
        return _to_organization_summary(membership)

    if membership.role != invite.role and membership.status != MemberStatus.ACTIVE:
        update_member_role(db, membership, role=invite.role)

    _finalize_invite_acceptance(db, invite=invite, user=user, membership=membership)
    db.commit()
    membership = get_membership(
        db,
        organization_id=invite.organization_id,
        user_id=user.id,
    )
    return _to_organization_summary(membership)


def accept_invitation(db: Session, membership: OrganizationMember) -> MemberSummary:
    if membership.status != MemberStatus.INVITED:
        raise ValidationAppError("No pending invitation to accept")

    pending_invite = get_pending_invite_by_email(
        db,
        organization_id=membership.organization_id,
        email=normalize_email(membership.user.email),
    )
    if pending_invite:
        _finalize_invite_acceptance(
            db,
            invite=pending_invite,
            user=membership.user,
            membership=membership,
        )
    else:
        _activate_membership(db, membership)
        record_audit_event(
            db,
            action=AuditAction.ORG_MEMBER_ACCEPT,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="organization_member",
            resource_id=membership.id,
        )

    db.commit()
    db.refresh(membership)
    return _to_member_summary(membership)


def revoke_invite(
    db: Session,
    membership: OrganizationMember,
    *,
    invite_id: uuid.UUID,
) -> None:
    invite = get_invite_by_id(
        db,
        organization_id=membership.organization_id,
        invite_id=invite_id,
    )
    if not invite or invite.status.value != "pending":
        raise NotFoundError("Invitation")

    revoke_organization_invite(db, invite)
    if invite.membership_id:
        member = get_organization_member_by_id(
            db,
            membership_id=invite.membership_id,
            organization_id=membership.organization_id,
        )
        if member and member.status == MemberStatus.INVITED:
            remove_organization_member(db, member)

    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_INVITE_REVOKE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization_invite",
        resource_id=invite.id,
        details={"invited_email": invite.email},
    )
    db.commit()


def update_member(
    db: Session,
    membership: OrganizationMember,
    *,
    target_membership_id: uuid.UUID,
    body: UpdateMemberRoleRequest,
) -> MemberSummary:
    if body.role is None and body.status is None:
        raise ValidationAppError("At least one field must be provided")

    target = get_organization_member_by_id(
        db,
        membership_id=target_membership_id,
        organization_id=membership.organization_id,
    )
    if not target:
        raise NotFoundError("Member")

    if target.role == OrganizationRole.OWNER and body.role is not None:
        raise ForbiddenError("Cannot change the owner's role directly")

    if membership.user_id == target.user_id and body.role is not None and body.role != membership.role:
        raise ForbiddenError("You cannot change your own role")

    if target.role == OrganizationRole.OWNER and body.status == MemberStatus.SUSPENDED:
        raise ForbiddenError("Cannot suspend the organization owner")

    updated = update_member_role(db, target, role=body.role, status=body.status)
    record_audit_event(
        db,
        action=AuditAction.ORG_MEMBER_UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization_member",
        resource_id=target.id,
        details=body.model_dump(exclude_none=True),
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
    if target.status != MemberStatus.ACTIVE:
        raise ValidationAppError("New owner must have an active membership")

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
