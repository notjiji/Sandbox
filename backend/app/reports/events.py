"""Audit event names for the reports feature."""


class ReportAuditAction:
    CREATE = "report.create"
    UPDATE = "report.update"
    GENERATE = "report.generate"
    REGENERATE = "report.regenerate"
    DOWNLOAD = "report.download"
    DELETE = "report.delete"
