"""Audit event names for the organizations feature."""


class OrganizationAuditAction:
    CREATE = "org.create"
    UPDATE = "org.update"
    CONFIG_CHANGED = "org.config_changed"
    ARCHIVE = "org.archive"
    RESTORE = "org.restore"
    DELETE = "org.delete"
