"""Audit Service — publish via the event bus; search/export/verify from audit_logs.

Business actions must succeed even if audit persistence or SIEM export fails.
"""

from __future__ import annotations

import csv
import io
import uuid
from datetime import datetime

from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.audit.hashing import compute_entry_hash
from app.audit.models import AuditLog
from app.audit.repositories.audit_repository import (
    get_audit_log_for_organization,
    list_chain_for_organization,
    search_audit_logs,
)
from app.audit.schemas import (
    AuditLogIntegrityResponse,
    AuditLogRecord,
    AuditLogSearchResponse,
)
from app.core.exceptions import NotFoundError
from app.core.report_engine.pdf import build_text_pdf
from app.events.bus import event_bus
from app.users.repositories.user_repository import get_primary_membership

EXPORT_LIMIT = 2000


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
    resource_id: uuid.UUID | str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | str | None = None,
    severity: str | None = None,
    details: dict | None = None,
) -> None:
    """Publish a meaningful event. Audit/SIEM/notifications subscribe independently."""
    event_bus.publish(
        action,
        details or {},
        db=db,
        user_id=user_id,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        entity_type=entity_type,
        entity_id=entity_id,
        severity=severity,
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
        prev_hash=record.prev_hash,
        entry_hash=record.entry_hash,
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


def get_organization_audit_log(
    db: Session,
    *,
    organization_id: uuid.UUID,
    log_id: uuid.UUID,
) -> AuditLogRecord:
    record = get_audit_log_for_organization(
        db,
        organization_id=organization_id,
        log_id=log_id,
    )
    if record is None:
        raise NotFoundError("AuditLog")
    return to_audit_log_record(record)


def verify_organization_audit_chain(
    db: Session,
    *,
    organization_id: uuid.UUID,
) -> AuditLogIntegrityResponse:
    rows = list_chain_for_organization(db, organization_id=organization_id)
    expected_prev = None
    for index, row in enumerate(rows):
        if expected_prev is None:
            expected_prev = row.prev_hash
        if row.prev_hash != expected_prev:
            return AuditLogIntegrityResponse(
                valid=False,
                checked=index,
                broken_at=str(row.id),
                reason="prev_hash does not match previous entry_hash",
            )
        computed = compute_entry_hash(
            prev_hash=row.prev_hash or "",
            record_id=row.id,
            organization_id=row.organization_id,
            user_id=row.user_id,
            action=row.action,
            resource_type=row.resource_type,
            resource_id=row.resource_id,
            severity=row.severity,
            details=row.details,
            created_at=row.created_at,
        )
        if computed != row.entry_hash:
            return AuditLogIntegrityResponse(
                valid=False,
                checked=index,
                broken_at=str(row.id),
                reason="entry_hash does not match canonical payload",
            )
        expected_prev = row.entry_hash
    return AuditLogIntegrityResponse(valid=True, checked=len(rows), broken_at=None, reason=None)


def _export_filters(**kwargs):
    return {key: value for key, value in kwargs.items() if key != "fmt"}


def export_organization_audit_logs(
    db: Session,
    *,
    organization_id: uuid.UUID,
    fmt: str = "csv",
    action: str | None = None,
    user_id: uuid.UUID | None = None,
    actor: str | None = None,
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    severity: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Response:
    records, _total = search_audit_logs(
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
        limit=EXPORT_LIMIT,
        offset=0,
    )
    fmt = (fmt or "csv").strip().lower()
    if fmt == "pdf":
        return _export_pdf(records)
    return _export_csv(records)


def _export_csv(records: list[AuditLog]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "id",
            "created_at",
            "action",
            "severity",
            "user_id",
            "entity_type",
            "entity_id",
            "details",
            "ip_address",
            "entry_hash",
        ]
    )
    for record in records:
        writer.writerow(
            [
                str(record.id),
                record.created_at.isoformat() if record.created_at else "",
                record.action,
                record.severity,
                str(record.user_id) if record.user_id else "",
                record.resource_type or "",
                str(record.resource_id) if record.resource_id else "",
                record.details or {},
                record.ip_address or "",
                record.entry_hash or "",
            ]
        )
    payload = buffer.getvalue()
    return StreamingResponse(
        iter([payload]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="audit-logs.csv"'},
    )


def _export_pdf(records: list[AuditLog]) -> Response:
    lines = [
        f"{record.created_at.isoformat() if record.created_at else ''}  "
        f"{(record.severity or 'info').upper():8}  {record.action}  "
        f"{(record.resource_type or '-')}"
        for record in records[:80]
    ]
    if not lines:
        lines = ["No audit events in this export."]
    pdf = build_text_pdf(title="Sandbox audit log export", lines=lines)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="audit-logs.pdf"'},
    )
