import uuid
from datetime import datetime, timedelta

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.audit.constants import AuditSeverity, normalize_severity
from app.audit.models import AuditLog
from app.users.models import User


def create_audit_log(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    severity: str = AuditSeverity.INFO.value,
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
        severity=normalize_severity(severity),
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(record)
    db.flush()
    return record


def list_audit_logs_for_resource(
    db: Session,
    *,
    resource_type: str,
    resource_id: uuid.UUID,
    limit: int = 50,
) -> list[AuditLog]:
    return (
        db.query(AuditLog)
        .filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id,
        )
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )


def _inclusive_end(date_to: datetime) -> datetime:
    if date_to.hour == 0 and date_to.minute == 0 and date_to.second == 0 and date_to.microsecond == 0:
        return date_to + timedelta(days=1)
    return date_to


def search_audit_logs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    actor: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    severity: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    exclude_prefixes: tuple[str, ...] = (),
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[AuditLog], int]:
    query = db.query(AuditLog).filter(AuditLog.organization_id == organization_id)

    for prefix in exclude_prefixes:
        query = query.filter(~AuditLog.action.startswith(prefix))

    if action:
        if action.endswith(".*"):
            query = query.filter(AuditLog.action.startswith(action[:-1]))
        elif action.endswith("."):
            query = query.filter(AuditLog.action.startswith(action))
        else:
            query = query.filter(AuditLog.action == action)

    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)

    if actor and actor.strip():
        needle = f"%{actor.strip()}%"
        query = query.join(User, User.id == AuditLog.user_id).filter(
            or_(
                User.email.ilike(needle),
                User.first_name.ilike(needle),
                User.last_name.ilike(needle),
                (User.first_name + " " + User.last_name).ilike(needle),
            )
        )

    if entity_type:
        query = query.filter(AuditLog.resource_type == entity_type)

    if entity_id is not None:
        query = query.filter(AuditLog.resource_id == entity_id)

    if asset_id is not None:
        asset_str = str(asset_id)
        query = query.filter(
            or_(
                (AuditLog.resource_type == "asset") & (AuditLog.resource_id == asset_id),
                AuditLog.details["asset_id"].as_string() == asset_str,
            )
        )

    if severity:
        query = query.filter(AuditLog.severity == normalize_severity(severity))

    if date_from is not None:
        query = query.filter(AuditLog.created_at >= date_from)

    if date_to is not None:
        query = query.filter(AuditLog.created_at < _inclusive_end(date_to))

    total = query.count()
    items = (
        query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit).all()
    )
    return items, total
