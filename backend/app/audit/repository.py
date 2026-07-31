import uuid

from sqlalchemy.orm import Session

from app.audit.models import AuditLog


def create_audit_log(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    record = AuditLog(
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(record)
    db.flush()
    return record
