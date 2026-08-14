"""Audit Service — one write path for every module.

Business actions must succeed even if audit persistence fails.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.audit.constants import severity_for_action
from app.audit.models import AuditLog
from app.audit.repositories.audit_repository import create_audit_log, search_audit_logs
from app.audit.schemas import AuditLogRecord, AuditLogSearchResponse
from app.core.logging import get_logger
from app.core.request_context import get_request_context
from app.users.repositories.user_repository import get_primary_membership

logger = get_logger("sandbox.audit")


def primary_organization_id(db: Session, user_id: uuid.UUID) -> uuid.UUID | None:
    membership = get_primary_membership(db, user_id)
    return membership.organization_id if membership else None


def _as_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None or isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None


def record_audit_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    severity: str | None = None,
    details: dict | None = None,
) -> None:
    """Persist a meaningful audit event. Never raises to the caller."""
    resolved_type = resource_type if resource_type is not None else entity_type
    resolved_id = _as_uuid(resource_id if resource_id is not None else entity_id)
    context = get_request_context()
    try:
        with db.begin_nested():
            create_audit_log(
                db,
                action=action,
                user_id=user_id,
                organization_id=organization_id,
                resource_type=resolved_type,
                resource_id=resolved_id,
                severity=severity_for_action(action, severity),
                details=details,
                ip_address=context.ip_address if context else None,
                user_agent=context.user_agent if context else None,
            )
    except Exception:
        logger.exception(
            "audit log write failed",
            extra={
                "action": action,
                "organization_id": str(organization_id) if organization_id else None,
                "user_id": str(user_id) if user_id else None,
            },
        )


def log(
    db: Session,
    *,
    organization_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    action: str,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    severity: str | None = None,
    details: dict | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | str | None = None,
) -> None:
    """Canonical logging method used by every feature module."""
    record_audit_event(
        db,
        action=action,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
        details=details,
    )


class AuditService:
    log = staticmethod(log)
    record = staticmethod(record_audit_event)


audit_service = AuditService()


def record_auth_event(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    resource_type: str | None = "session",
    resource_id: uuid.UUID | None = None,
    details: dict | None = None,
    severity: str | None = None,
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
        severity=severity,
    )


def to_audit_log_record(record: AuditLog) -> AuditLogRecord:
    entity_type = record.resource_type
    entity_id = str(record.resource_id) if record.resource_id else None
    return AuditLogRecord(
        id=str(record.id),
        organization_id=str(record.organization_id) if record.organization_id else None,
        user_id=str(record.user_id) if record.user_id else None,
        action=record.action,
        entity_type=entity_type,
        entity_id=entity_id,
        resource_type=entity_type,
        resource_id=entity_id,
        severity=record.severity,
        details=record.details,
        ip_address=record.ip_address,
        user_agent=record.user_agent,
        created_at=record.created_at,
    )


def search_organization_audit_logs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    page: int = 1,
    limit: int = 20,
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    actor: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    severity: str | None = None,
    date_from=None,
    date_to=None,
    exclude_prefixes: tuple[str, ...] = (),
) -> AuditLogSearchResponse:
    offset = (page - 1) * limit
    records, total = search_audit_logs(
        db,
        organization_id=organization_id,
        action=action,
        user_id=user_id,
        actor=actor,
        entity_type=entity_type,
        entity_id=entity_id,
        asset_id=asset_id,
        severity=severity,
        date_from=date_from,
        date_to=date_to,
        exclude_prefixes=exclude_prefixes,
        limit=limit,
        offset=offset,
    )
    return AuditLogSearchResponse(
        items=[to_audit_log_record(record) for record in records],
        total=total,
        page=page,
        limit=limit,
    )
