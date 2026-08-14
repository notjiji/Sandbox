"""Audit subscriber — writes the hash-chained audit row for every domain event."""

from __future__ import annotations

from app.audit.persistence import persist_audit_log
from app.events.bus import DomainEvent


def persist_audit_event(event: DomainEvent) -> None:
    if event.db is None:
        return
    details = dict(event.payload)
    record = persist_audit_log(
        event.db,
        action=event.name,
        user_id=event.user_id,
        organization_id=event.organization_id,
        resource_type=event.resource_type,
        resource_id=event.resource_id,
        entity_type=event.entity_type,
        entity_id=event.entity_id,
        severity=event.severity,
        details=details or None,
    )
    event.record = record
