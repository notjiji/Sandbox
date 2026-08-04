"""Audit event names for the projects feature."""


class ProjectAuditAction:
    CREATE = "project.create"
    UPDATE = "project.update"
    ARCHIVE = "project.archive"
    RESTORE = "project.restore"
    DELETE = "project.delete"
