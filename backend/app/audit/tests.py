"""Audit service unit tests."""

from __future__ import annotations

from app.audit.constants import AuditSeverity, severity_for_action
from app.audit.events import AuditAction
from app.audit.hashing import GENESIS_HASH
from app.audit.models import AuditLog
from app.audit.service import audit_service, record_audit_event
from app.events.bus import event_bus
from app.events.names import normalize_action


def test_audit_module_imports() -> None:
    assert AuditLog.__tablename__ == "audit_logs"
    assert AuditAction.AUTH_LOGIN == "auth.login"
    assert callable(record_audit_event)
    assert callable(audit_service.log)
    assert callable(event_bus.publish)


def test_severity_defaults() -> None:
    assert severity_for_action("asset.create") == AuditSeverity.INFO.value
    assert severity_for_action("scan.failed") == AuditSeverity.WARNING.value
    assert severity_for_action("scan.plugin_failed") == AuditSeverity.ERROR.value
    assert severity_for_action("auth.account_disabled") == AuditSeverity.CRITICAL.value
    assert severity_for_action("scan.failed", "ERROR") == AuditSeverity.ERROR.value


def test_normalize_action_aliases() -> None:
    assert normalize_action("SCAN_COMPLETED") == "scan.completed"
    assert normalize_action("ASSET_CREATED") == "asset.create"
    assert normalize_action("scan.failed") == "scan.failed"
    assert normalize_action("ERROR") is not None


def test_record_audit_event_persists_severity(db) -> None:
    record_audit_event(db, action="scan.failed", details={"asset_name": "vinca.family"})
    row = (
        db.query(AuditLog)
        .filter(AuditLog.action == "scan.failed")
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert row is not None
    assert row.severity == "warning"
    assert row.details["asset_name"] == "vinca.family"
    assert row.entry_hash
    assert row.prev_hash == GENESIS_HASH


def test_log_accepts_entity_aliases(db) -> None:
    import uuid

    entity_id = uuid.uuid4()
    audit_service.log(
        db,
        action="ASSET_CREATED",
        entity_type="asset",
        entity_id=entity_id,
        details={"asset_name": "vinca.family"},
    )
    row = db.query(AuditLog).filter(AuditLog.resource_id == entity_id).one()
    assert row.resource_type == "asset"
    assert row.action == "asset.create"
    assert row.severity == "info"


def test_hash_chain_links_and_verifies(db) -> None:
    import uuid

    marker = uuid.uuid4()
    record_audit_event(db, action="asset.create", entity_id=marker, details={"n": 1})
    record_audit_event(db, action="scan.completed", entity_id=marker, details={"n": 2})
    rows = (
        db.query(AuditLog)
        .filter(AuditLog.resource_id == marker)
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        .all()
    )
    assert len(rows) == 2
    assert rows[1].prev_hash == rows[0].entry_hash
    assert rows[0].entry_hash
    assert rows[1].entry_hash


def test_audit_write_failure_does_not_raise(db, monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("audit storage unavailable")

    before = db.query(AuditLog).count()
    monkeypatch.setattr("app.audit.persistence.create_audit_log", _boom)
    record_audit_event(db, action="asset.create")
    assert db.query(AuditLog).count() == before


def test_event_bus_continues_after_handler_failure() -> None:
    seen: list[str] = []

    def _fail(_event) -> None:
        raise RuntimeError("subscriber down")

    def _ok(event) -> None:
        seen.append(event.name)

    event_bus.subscribe(_fail)
    event_bus.subscribe(_ok)
    event_bus.publish("asset.create", {"asset_name": "vinca.family"})
    assert "asset.create" in seen
    event_bus._handlers.remove(_fail)
    event_bus._handlers.remove(_ok)
