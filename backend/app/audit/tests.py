"""Audit service unit tests."""

from __future__ import annotations

from app.audit.constants import AuditSeverity, severity_for_action
from app.audit.events import AuditAction
from app.audit.models import AuditLog
from app.audit.service import audit_service, record_audit_event


def test_audit_module_imports() -> None:
    assert AuditLog.__tablename__ == "audit_logs"
    assert AuditAction.AUTH_LOGIN == "auth.login"
    assert callable(record_audit_event)
    assert callable(audit_service.log)


def test_severity_defaults() -> None:
    assert severity_for_action("asset.create") == AuditSeverity.INFO.value
    assert severity_for_action("scan.failed") == AuditSeverity.WARNING.value
    assert severity_for_action("scan.plugin_failed") == AuditSeverity.ERROR.value
    assert severity_for_action("auth.account_disabled") == AuditSeverity.CRITICAL.value
    assert severity_for_action("scan.failed", "ERROR") == AuditSeverity.ERROR.value


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


def test_log_accepts_entity_aliases(db) -> None:
    import uuid

    entity_id = uuid.uuid4()
    audit_service.log(
        db,
        action="asset.create",
        entity_type="asset",
        entity_id=entity_id,
        details={"asset_name": "vinca.family"},
    )
    row = db.query(AuditLog).filter(AuditLog.resource_id == entity_id).one()
    assert row.resource_type == "asset"
    assert row.severity == "info"


def test_audit_write_failure_does_not_raise(db, monkeypatch) -> None:
    def _boom(*_args, **_kwargs):
        raise RuntimeError("audit storage unavailable")

    before = db.query(AuditLog).count()
    monkeypatch.setattr("app.audit.service.create_audit_log", _boom)
    record_audit_event(db, action="asset.create")
    assert db.query(AuditLog).count() == before
