import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import ForbiddenError, NotFoundError, ValidationAppError
from app.members.enums import MemberStatus, OrganizationRole
from app.members.events import MemberAuditAction
from app.members.models import OrganizationMember
from app.members.repositories.member_repository import (
    get_membership,
    get_organization_member_by_id,
    list_organization_members,
    remove_organization_member,
    update_member_role,
)
from app.members.schemas import (
    MemberSummary,
    TransferOwnershipRequest,
    UpdateMemberRoleRequest,
)
from app.audit.service import record_audit_event


def to_member_summary(
    membership: OrganizationMember,
    *,
    invite_id: str | None = None,
) -> MemberSummary:
    user = membership.user
    return MemberSummary(
        membership_id=str(membership.id),
        invite_id=invite_id,
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=membership.role,
        status=membership.status.value,
        joined_at=membership.joined_at,
        last_login=user.last_login,
        invited_at=membership.created_at,
    )


def list_current_organization_members(
    db: Session,
    membership: OrganizationMember,
) -> list[MemberSummary]:
    members = list_organization_members(db, membership.organization_id)
    return [to_member_summary(member) for member in members]


def accept_invitation(db: Session, membership: OrganizationMember) -> MemberSummary:
    from app.members.services.invite_service import finalize_invite_acceptance
    from app.organizations.repositories.invite_repository import get_pending_invite_by_email
    from app.auth.schemas import normalize_email

    if membership.status != MemberStatus.INVITED:
        raise ValidationAppError("No pending invitation to accept")

    pending_invite = get_pending_invite_by_email(
        db,
        organization_id=membership.organization_id,
        email=normalize_email(membership.user.email),
    )
    if pending_invite:
        finalize_invite_acceptance(
            db,
            invite=pending_invite,
            user=membership.user,
            membership=membership,
        )
    else:
        update_member_role(db, membership, status=MemberStatus.ACTIVE)
        record_audit_event(
            db,
            action=MemberAuditAction.ACCEPT,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            resource_type="organization_member",
            resource_id=membership.id,
        )

    db.commit()
    db.refresh(membership)
    return to_member_summary(membership)


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
        action=MemberAuditAction.UPDATE,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization_member",
        resource_id=target.id,
        details=body.model_dump(exclude_none=True),
    )
    db.commit()
    db.refresh(updated)
    return to_member_summary(updated)


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
        action=MemberAuditAction.REMOVE,
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
        action=MemberAuditAction.OWNERSHIP_TRANSFER,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        resource_type="organization",
        resource_id=membership.organization_id,
        details={"new_owner_user_id": str(target.user_id)},
    )
    db.commit()
    db.refresh(target)
    return to_member_summary(target)
