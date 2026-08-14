"""Audit event names for the scans feature."""


class ScanAuditAction:
    CREATE = "scan.create"
    RUN = "scan.run"
    STARTED = "scan.started"
    COMPLETED = "scan.completed"
    FAILED = "scan.failed"
    CANCEL = "scan.cancel"
    PLUGIN_FAILED = "scan.plugin_failed"
