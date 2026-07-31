import uuid

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationAppError
from app.core.security import (
    generate_opaque_token,
    get_organization_invite_expiry,
    hash_token,
)
from app.members.enums import MemberStatus, OrganizationRole
from app.members.events import MemberAuditAction
from app.members.models import OrganizationMember
from app.members.repositories.member_repository import (
    add_organization_member,
    get_membership,
    get_organization_member_by_id,
    remove_organization_member,
    update_member_role,
)
from app.members.schemas import (
    InviteMemberRequest,
    InvitePreview,
    InviteResult,
    PendingInviteSummary,
)
from app.auth.schemas import normalize_email
from app.audit.service import record_audit_event
from app.members.email import send_organization_invite_email
from app.users.models import User
from app.users.repositories.user_repository import get_user_by_email
from app.organizations.repositories.invite_repository import (
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
from app.organizations.models import Organization
from app.organizations.schemas import OrganizationSummary
from app.organizations.services.organization_service import to_organization_summary


def to_pending_invite_summary(invite) -> PendingInviteSummary:
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


def activate_membership(db: Session, membership: OrganizationMember) -> OrganizationMember:
    return update_member_role(
        db,
        membership,
        status=MemberStatus.ACTIVE,
    )


def finalize_invite_acceptance(
    db: Session,
    *,
    invite,
    user: User,
    membership: OrganizationMember,
) -> OrganizationMember:
    if membership.status != MemberStatus.ACTIVE:
        activate_membership(db, membership)
    if invite.status.value != "accepted":
        mark_invite_accepted(db, invite)
    record_audit_event(
        db,
        action=MemberAuditAction.ACCEPT,
        user_id=user.id,
        organization_id=invite.organization_id,
        resource_type="organization_member",
        resource_id=membership.id,
        details={"invite_id": str(invite.id)},
    )
    return membership


def list_current_pending_invites(
    db: Session,
    membership: OrganizationMember,
) -> list[PendingInviteSummary]:
    invites = list_pending_invites_for_organization(db, organization_id=membership.organization_id)
    return [to_pending_invite_summary(invite) for invite in invites]


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

    existing = None
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
        action=MemberAuditAction.INVITE,
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
        return to_organization_summary(membership)

    if membership.role != invite.role and membership.status != MemberStatus.ACTIVE:
        update_member_role(db, membership, role=invite.role)

    finalize_invite_acceptance(db, invite=invite, user=user, membership=membership)
    db.commit()
    membership = get_membership(
        db,
        organization_id=invite.organization_id,
        user_id=user.id,
    )
    return to_organization_summary(membership)


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
        action=MemberAuditAction.INVITE_REVOKE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization_invite",
        resource_id=invite.id,
        details={"invited_email": invite.email},
    )
    db.commit()
