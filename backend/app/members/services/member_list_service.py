from sqlalchemy.orm import Session

from app.members.enums import MemberStatus, OrganizationRole
from app.members.models import OrganizationMember
from app.members.repositories.member_repository import list_organization_members
from app.members.schemas import MemberListQuery, MemberListResponse, MemberSummary
from app.members.services.member_list import (
    member_row_from_invite,
    member_row_from_membership,
    row_matches_search,
    row_matches_status_filter,
    sort_member_rows,
)
from app.organizations.repositories.invite_repository import list_pending_invites_for_organization


def _to_summary(row) -> MemberSummary:
    return MemberSummary(
        membership_id=row.membership_id,
        invite_id=row.invite_id,
        user_id=row.user_id,
        email=row.email,
        first_name=row.first_name,
        last_name=row.last_name,
        role=row.role,
        status=row.status,
        joined_at=row.joined_at,
        last_login=row.last_login,
        invited_at=row.invited_at,
    )


def _build_member_rows(db: Session, organization_id) -> list:
    members = list_organization_members(db, organization_id)
    pending_invites = list_pending_invites_for_organization(db, organization_id=organization_id)

    invite_by_membership = {
        str(invite.membership_id): invite
        for invite in pending_invites
        if invite.membership_id is not None
    }
    invite_by_email = {invite.email: invite for invite in pending_invites}

    rows = []
    seen_invite_ids: set[str] = set()

    for membership in members:
        invite = invite_by_membership.get(str(membership.id))
        if invite:
            seen_invite_ids.add(str(invite.id))
        elif membership.status == MemberStatus.INVITED:
            invite = invite_by_email.get(membership.user.email)
            if invite:
                seen_invite_ids.add(str(invite.id))
        rows.append(member_row_from_membership(membership, invite=invite))

    for invite in pending_invites:
        if str(invite.id) in seen_invite_ids:
            continue
        rows.append(member_row_from_invite(invite))

    return rows


def list_organization_members_paginated(
    db: Session,
    membership: OrganizationMember,
    *,
    query: MemberListQuery,
) -> MemberListResponse:
    rows = _build_member_rows(db, membership.organization_id)

    if query.role is not None:
        rows = [row for row in rows if row.role == query.role]

    rows = [row for row in rows if row_matches_status_filter(row, query.status)]
    rows = [row for row in rows if row_matches_search(row, query.search)]
    rows = sort_member_rows(rows, sort=query.sort, order=query.order)

    total = len(rows)
    start = (query.page - 1) * query.limit
    end = start + query.limit
    page_rows = rows[start:end]

    return MemberListResponse(
        items=[_to_summary(row) for row in page_rows],
        total=total,
        page=query.page,
        limit=query.limit,
    )
