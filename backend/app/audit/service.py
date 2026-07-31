import uuid

from sqlalchemy.orm import Session

from app.audit.repositories.audit_repository import create_audit_log
from app.core.request_context import get_request_context
from app.users.repositories.user_repository import get_primary_membership


def primary_organization_id(db: Session, user_id: uuid.UUID) -> uuid.UUID | None:
    membership = get_primary_membership(db, user_id)
    return membership.organization_id if membership else None


def record_audit_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    context = get_request_context()
    create_audit_log(
        db,
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=context.ip_address if context else None,
        user_agent=context.user_agent if context else None,
    )


def record_auth_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = "session",
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
) -> None:
    org_id = primary_organization_id(db, user_id) if user_id else None
    record_audit_event(
        db,
        action=action,
        user_id=user_id,
        organization_id=org_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
    )
