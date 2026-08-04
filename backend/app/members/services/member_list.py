from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.members.enums import MemberStatus, OrganizationRole
from app.members.models import OrganizationMember
from app.organizations.invites import OrganizationInvite


@dataclass
class MemberListRow:
    membership_id: str | None
    invite_id: str | None
    user_id: str | None
    email: str
    first_name: str | None
    last_name: str | None
    role: OrganizationRole
    status: str
    joined_at: datetime | None
    last_login: datetime | None
    invited_at: datetime | None


def member_row_from_membership(
    membership: OrganizationMember,
    *,
    invite: OrganizationInvite | None = None,
) -> MemberListRow:
    user = membership.user
    status = membership.status.value
    return MemberListRow(
        membership_id=str(membership.id),
        invite_id=str(invite.id) if invite else None,
        user_id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=membership.role,
        status=status,
        joined_at=membership.joined_at,
        last_login=user.last_login,
        invited_at=invite.created_at if invite else membership.created_at,
    )


def member_row_from_invite(invite: OrganizationInvite) -> MemberListRow:
    return MemberListRow(
        membership_id=None,
        invite_id=str(invite.id),
        user_id=None,
        email=invite.email,
        first_name=None,
        last_name=None,
        role=invite.role,
        status="pending",
        joined_at=None,
        last_login=None,
        invited_at=invite.created_at,
    )


def row_matches_status_filter(row: MemberListRow, status_filter: str | None) -> bool:
    if not status_filter:
        return True
    normalized = status_filter.lower()
    if normalized == "active":
        return row.status == MemberStatus.ACTIVE.value
    if normalized == "suspended":
        return row.status == MemberStatus.SUSPENDED.value
    if normalized == "pending":
        return row.status in {MemberStatus.INVITED.value, "pending"}
    return row.status == normalized


def row_matches_search(row: MemberListRow, search: str | None) -> bool:
    if not search:
        return True
    needle = search.lower().strip()
    if not needle:
        return True
    haystacks = [
        row.email,
        row.first_name or "",
        row.last_name or "",
        f"{row.first_name or ''} {row.last_name or ''}".strip(),
        row.role.value,
        row.status,
    ]
    return any(needle in value.lower() for value in haystacks if value)


def sort_member_rows(
    rows: list[MemberListRow],
    *,
    sort: str,
    order: str,
) -> list[MemberListRow]:
    reverse = order == "desc"

    def sort_key(row: MemberListRow):
        if sort == "email":
            return row.email.lower()
        if sort == "role":
            return row.role.value
        if sort == "status":
            return row.status
        if sort == "joined_at":
            return row.joined_at or datetime.min
        if sort == "last_login":
            return row.last_login or datetime.min
        last = (row.last_name or "").lower()
        first = (row.first_name or row.email).lower()
        return (last, first)

    return sorted(rows, key=sort_key, reverse=reverse)
