import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session, joinedload

from app.members.enums import OrganizationRole
from app.organizations.invites import InviteStatus, OrganizationInvite


def get_pending_invite_by_email(
    db: Session,
    *,
    organization_id: uuid.UUID,
    email: str,
) -> OrganizationInvite | None:
    return (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.organization_id == organization_id,
            OrganizationInvite.email == email,
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .first()
    )


def get_invite_by_token_hash(db: Session, *, token_hash: str) -> OrganizationInvite | None:
    return (
        db.query(OrganizationInvite)
        .options(
            joinedload(OrganizationInvite.organization),
            joinedload(OrganizationInvite.membership),
            joinedload(OrganizationInvite.inviter),
        )
        .filter(OrganizationInvite.token_hash == token_hash)
        .first()
    )


def get_invite_by_id(
    db: Session,
    *,
    organization_id: uuid.UUID,
    invite_id: uuid.UUID,
) -> OrganizationInvite | None:
    return (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.id == invite_id,
            OrganizationInvite.organization_id == organization_id,
        )
        .first()
    )


def list_pending_invites_for_organization(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> list[OrganizationInvite]:
    return (
        db.query(OrganizationInvite)
        .filter(
            OrganizationInvite.organization_id == organization_id,
            OrganizationInvite.status == InviteStatus.PENDING,
        )
        .order_by(OrganizationInvite.created_at.desc())
        .all()
    )


def create_organization_invite(
    db: Session,
    *,
    organization_id: uuid.UUID,
    email: str,
    role: OrganizationRole,
    token_hash: str,
    invited_by: uuid.UUID,
    expires_at: datetime,
    membership_id: uuid.UUID | None = None,
) -> OrganizationInvite:
    invite = OrganizationInvite(
        organization_id=organization_id,
        email=email,
        role=role,
        token_hash=token_hash,
        invited_by=invited_by,
        membership_id=membership_id,
        status=InviteStatus.PENDING,
        expires_at=expires_at,
    )
    db.add(invite)
    db.flush()
    return invite


def refresh_organization_invite(
    db: Session,
    invite: OrganizationInvite,
    *,
    token_hash: str,
    expires_at: datetime,
    role: OrganizationRole,
    membership_id: uuid.UUID | None = None,
) -> OrganizationInvite:
    invite.token_hash = token_hash
    invite.expires_at = expires_at
    invite.role = role
    invite.status = InviteStatus.PENDING
    invite.accepted_at = None
    if membership_id is not None:
        invite.membership_id = membership_id
    db.add(invite)
    db.flush()
    return invite


def mark_invite_accepted(db: Session, invite: OrganizationInvite) -> OrganizationInvite:
    invite.status = InviteStatus.ACCEPTED
    invite.accepted_at = datetime.now(UTC)
    db.add(invite)
    db.flush()
    return invite


def revoke_organization_invite(db: Session, invite: OrganizationInvite) -> None:
    invite.status = InviteStatus.REVOKED
    db.add(invite)


def is_invite_valid(invite: OrganizationInvite) -> bool:
    if invite.status != InviteStatus.PENDING:
        return False
    return invite.expires_at > datetime.now(UTC)
