"""Persist an audit row with hash chaining. Application code never updates or deletes rows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.audit.constants import severity_for_action
from app.audit.hashing import GENESIS_HASH, compute_entry_hash
from app.audit.models import AuditLog
from app.audit.repositories.audit_repository import create_audit_log, latest_entry_hash
from app.core.logging import get_logger
from app.core.request_context import get_request_context
from app.events.names import normalize_action

logger = get_logger("sandbox.audit")


def persist_audit_log(
    db: Session,
    *,
    action: str,
    user_id: uuid.UUID | None = None,
    organization_id: uuid.UUID | None = None,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    severity: str | None = None,
    details: dict | None = None,
) -> AuditLog | None:
    resolved_action = normalize_action(action) or action
    resolved_type = resource_type if resource_type is not None else entity_type
    resolved_id = _as_uuid(resource_id if resource_id is not None else entity_id)
    resolved_severity = severity_for_action(resolved_action, severity)
    context = get_request_context()
    record_id = uuid.uuid4()
    created_at = datetime.now(UTC)
    try:
        with db.begin_nested():
            prev_hash = latest_entry_hash(db, organization_id=organization_id) or GENESIS_HASH
            entry_hash = compute_entry_hash(
                prev_hash=prev_hash,
                record_id=record_id,
                organization_id=organization_id,
                user_id=user_id,
                action=resolved_action,
                resource_type=resolved_type,
                resource_id=resolved_id,
                severity=resolved_severity,
                details=details,
                created_at=created_at,
            )
            return create_audit_log(
                db,
                record_id=record_id,
                action=resolved_action,
                user_id=user_id,
                organization_id=organization_id,
                resource_type=resolved_type,
                resource_id=resolved_id,
                severity=resolved_severity,
                details=details,
                ip_address=context.ip_address if context else None,
                user_agent=context.user_agent if context else None,
                created_at=created_at,
                prev_hash=prev_hash,
                entry_hash=entry_hash,
            )
    except Exception:
        logger.exception(
            "audit log write failed",
            extra={
                "action": resolved_action,
                "organization_id": str(organization_id) if organization_id else None,
                "user_id": str(user_id) if user_id else None,
            },
        )
        return None


def _as_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None or isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, TypeError):
        return None
