"""Audit service unit tests."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.audit.constants import AuditSeverity, severity_for_action
from app.audit.events import AuditAction
from app.audit.hashing import GENESIS_HASH
from app.audit.models import AuditLog
from app.audit.service import audit_service, record_audit_event
from app.events.bus import event_bus
from app.events.names import normalize_action
from app.organizations.models import Organization


def _create_org(db: Session, *, name: str) -> uuid.UUID:
    org = Organization(
        name=name,
        slug=f"{name.lower().replace(' ', '-')}-{uuid.uuid4().hex[:8]}",
        settings={},
    )
    db.add(org)
    db.flush()
    return org.id


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


def test_hash_chain_create_link_and_verify(db) -> None:
    """Create → hash → next prev_hash → integrity succeeds. Chains are per organization."""
    from app.audit.service import verify_organization_audit_chain

    org_a = _create_org(db, name="Chain A")
    org_b = _create_org(db, name="Chain B")
    marker = uuid.uuid4()

    record_audit_event(
        db,
        action="asset.create",
        organization_id=org_a,
        entity_id=marker,
        details={"n": 1},
    )
    record_audit_event(
        db,
        action="scan.completed",
        organization_id=org_a,
        entity_id=marker,
        details={"n": 2},
    )
    record_audit_event(
        db,
        action="asset.create",
        organization_id=org_b,
        entity_id=marker,
        details={"other_org": True},
    )

    rows_a = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_a, AuditLog.resource_id == marker)
        .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        .all()
    )
    assert len(rows_a) == 2
    assert rows_a[0].entry_hash
    assert rows_a[0].prev_hash == GENESIS_HASH
    assert rows_a[1].prev_hash == rows_a[0].entry_hash
    assert rows_a[1].entry_hash != rows_a[0].entry_hash

    row_b = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_b, AuditLog.resource_id == marker)
        .one()
    )
    assert row_b.prev_hash == GENESIS_HASH
    assert row_b.entry_hash != rows_a[0].entry_hash

    result = verify_organization_audit_chain(db, organization_id=org_a)
    assert result.valid is True
    assert result.checked == 2
    assert result.broken_at is None
    assert result.reason is None

    other = verify_organization_audit_chain(db, organization_id=org_b)
    assert other.valid is True
    assert other.checked == 1


def test_hash_chain_skips_legacy_rows_without_hashes(db) -> None:
    from app.audit.repositories.audit_repository import create_audit_log
    from app.audit.service import verify_organization_audit_chain

    org_id = _create_org(db, name="Legacy Skip")
    create_audit_log(
        db,
        action="asset.create",
        organization_id=org_id,
        severity="info",
        details={"legacy": True},
        prev_hash=None,
        entry_hash=None,
    )
    record_audit_event(
        db,
        action="scan.completed",
        organization_id=org_id,
        details={"hashed": True},
    )
    db.flush()

    hashed = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id, AuditLog.entry_hash.isnot(None))
        .all()
    )
    legacy = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id, AuditLog.entry_hash.is_(None))
        .all()
    )
    assert len(legacy) == 1
    assert len(hashed) == 1

    result = verify_organization_audit_chain(db, organization_id=org_id)
    assert result.valid is True
    assert result.checked == 1


def test_hash_chain_detects_tampered_record(db) -> None:
    """SQLite tests can UPDATE rows. Postgres trigger blocks UPDATE; verify still
    detects a restored or trigger-bypassed mutation."""
    from sqlalchemy.orm.attributes import flag_modified

    from app.audit.service import verify_organization_audit_chain

    org_id = _create_org(db, name="Tamper Detect")
    record_audit_event(db, action="asset.create", organization_id=org_id, details={"ok": True})
    record_audit_event(db, action="scan.completed", organization_id=org_id, details={"ok": True})
    db.flush()

    intact = verify_organization_audit_chain(db, organization_id=org_id)
    assert intact.valid is True
    assert intact.checked == 2

    victim = (
        db.query(AuditLog)
        .filter(AuditLog.organization_id == org_id, AuditLog.action == "scan.completed")
        .one()
    )
    victim.details = {"ok": True, "tampered": True}
    flag_modified(victim, "details")
    db.flush()
    db.refresh(victim)

    broken = verify_organization_audit_chain(db, organization_id=org_id)
    assert broken.valid is False
    assert broken.broken_at == str(victim.id)
    assert broken.reason == "entry_hash does not match canonical payload"
    assert broken.checked == 1


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
