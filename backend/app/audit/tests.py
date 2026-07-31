"""Audit feature tests — expand as the module grows."""


def test_audit_module_imports() -> None:
    from app.audit.events import AuditAction
    from app.audit.models import AuditLog
    from app.audit.service import record_audit_event

    assert AuditLog.__tablename__ == "audit_logs"
    assert AuditAction.AUTH_LOGIN == "auth.login"
    assert callable(record_audit_event)
