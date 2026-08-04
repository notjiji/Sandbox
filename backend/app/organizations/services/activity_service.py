import uuid

from sqlalchemy.orm import Session

from app.audit.models import AuditLog
from app.members.enums import OrganizationRole
from app.organizations.repositories.overview_repository import list_organization_activity
from app.organizations.schemas_activity import ActivityActor, ActivityEvent, OrganizationActivityResponse
from app.users.models import User


def _actor_display(user: User | None) -> ActivityActor:
    if user is None:
        return ActivityActor(name="System")
    name = f"{user.first_name} {user.last_name}".strip() or user.email
    return ActivityActor(id=str(user.id), name=name, email=user.email)


def _details(record: AuditLog) -> dict:
    return record.details or {}


def _detail_str(record: AuditLog, key: str, fallback: str = "") -> str:
    value = _details(record).get(key)
    if value is None:
        return fallback
    return str(value)


def _role_label(role: str) -> str:
    try:
        return OrganizationRole(role).value.replace("_", " ")
    except ValueError:
        return role.replace("_", " ")


def _category_for_action(action: str) -> str:
    if action.startswith("org.member") or action.startswith("org.ownership"):
        return "members"
    if action.startswith("asset."):
        return "assets"
    if action.startswith("scan."):
        return "scans"
    if action.startswith("report."):
        return "reports"
    if action.startswith("finding."):
        return "findings"
    if action.startswith("project."):
        return "projects"
    if action.startswith("org.risk"):
        return "security"
    if action.startswith("org."):
        return "organization"
    return "system"


def _build_href(record: AuditLog) -> str | None:
    details = _details(record)
    project_id = details.get("project_id")
    resource_type = record.resource_type
    resource_id = str(record.resource_id) if record.resource_id else None

    if resource_type == "project" and resource_id:
        return f"/projects/{resource_id}"
    if resource_type == "asset" and resource_id and project_id:
        return f"/projects/{project_id}/assets/{resource_id}"
    if resource_type == "scan" and project_id:
        asset_id = details.get("asset_id")
        if asset_id:
            return f"/projects/{project_id}/assets/{asset_id}/scans"
        return f"/projects/{project_id}/assets"
    if resource_type == "report" and project_id:
        return f"/projects/{project_id}/reports"
    if resource_type == "finding" and project_id:
        return f"/projects/{project_id}/findings"
    if resource_type in {"organization_member", "organization_invite"}:
        return "/organization/members"
    if resource_type == "organization":
        return "/organization/settings"
    return None


def _build_message(record: AuditLog, actor_name: str) -> str:
    action = record.action
    details = _details(record)

    if action == "org.member_invite":
        email = details.get("invited_email", "someone")
        role = _role_label(str(details.get("role", "member")))
        return f"{actor_name} invited {email} as {role}"
    if action == "org.member_invite_revoke":
        return f"{actor_name} revoked an invitation for {details.get('invited_email', 'someone')}"
    if action == "org.member_invite_resend":
        return f"{actor_name} resent an invitation to {details.get('invited_email', 'someone')}"
    if action == "org.member_accept":
        return f"{actor_name} joined the organization"
    if action == "org.member_update":
        return f"{actor_name} updated a member role"
    if action == "org.member_remove":
        return f"{actor_name} removed a member from the organization"
    if action == "org.ownership_transfer":
        return f"{actor_name} transferred organization ownership"

    if action == "org.create":
        return f"{actor_name} created the organization"
    if action == "org.update":
        return f"{actor_name} updated organization settings"
    if action == "org.archive":
        return f"{actor_name} archived the organization"
    if action == "org.delete":
        return f"{actor_name} deleted the organization"
    if action == "org.risk_score_changed":
        previous = details.get("previous_score")
        current = details.get("current_score")
        if previous is not None and current is not None:
            return f"Risk score changed from {previous} to {current}"
        return "Organization risk score updated"

    if action == "project.create":
        return f"{actor_name} created project {details.get('name', 'Untitled')}"
    if action == "project.update":
        return f"{actor_name} updated project {details.get('name', 'settings')}"
    if action == "project.archive":
        return f"{actor_name} archived a project"
    if action == "project.restore":
        return f"{actor_name} restored a project"
    if action == "project.delete":
        return f"{actor_name} deleted a project"

    if action == "asset.create":
        return f"{actor_name} added asset {details.get('name', 'Untitled')}"
    if action == "asset.update":
        return f"{actor_name} updated asset {details.get('name', 'settings')}"
    if action == "asset.archive":
        return f"{actor_name} archived an asset"
    if action == "asset.restore":
        return f"{actor_name} restored an asset"
    if action == "asset.delete":
        return f"{actor_name} removed an asset"

    if action == "scan.create":
        return f"{actor_name} scheduled a scan"
    if action == "scan.run":
        return f"{actor_name} started a scan"
    if action == "scan.cancel":
        return f"{actor_name} cancelled a scan"

    if action == "report.create":
        return f"{actor_name} created report {details.get('name', 'Untitled')}"
    if action == "report.update":
        return f"{actor_name} updated report {details.get('name', 'settings')}"
    if action == "report.generate":
        return f"{actor_name} generated a report"
    if action == "report.delete":
        return f"{actor_name} deleted a report"

    if action == "finding.update":
        return f"{actor_name} updated a finding"
    if action == "finding.review":
        return f"{actor_name} reviewed a finding"

    label = action.split(".")[-1].replace("_", " ")
    resource = record.resource_type or "item"
    return f"{actor_name} {label} {resource}"


def present_activity_event(record: AuditLog, users_by_id: dict[uuid.UUID, User]) -> ActivityEvent:
    user = users_by_id.get(record.user_id) if record.user_id else None
    actor = _actor_display(user)
    return ActivityEvent(
        id=str(record.id),
        message=_build_message(record, actor.name),
        category=_category_for_action(record.action),
        action=record.action,
        actor=actor if user else None,
        resource_type=record.resource_type,
        resource_id=str(record.resource_id) if record.resource_id else None,
        href=_build_href(record),
        created_at=record.created_at,
    )


def _load_users(db: Session, records: list[AuditLog]) -> dict[uuid.UUID, User]:
    user_ids = {record.user_id for record in records if record.user_id}
    if not user_ids:
        return {}
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    return {user.id: user for user in users}


def present_activity_events(db: Session, records: list[AuditLog]) -> list[ActivityEvent]:
    users_by_id = _load_users(db, records)
    return [present_activity_event(record, users_by_id) for record in records]


def get_organization_activity(
    db: Session,
    *,
    organization_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
) -> OrganizationActivityResponse:
    offset = (page - 1) * limit
    records, total = list_organization_activity(
        db,
        organization_id=organization_id,
        limit=limit,
        offset=offset,
    )
    items = present_activity_events(db, records)
    return OrganizationActivityResponse(
        items=items,
        total=total,
        page=page,
        limit=limit,
    )
