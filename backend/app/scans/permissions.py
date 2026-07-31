"""Scan feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

SCAN_READ = Permission.SCAN_READ
SCAN_CREATE = Permission.SCAN_CREATE
SCAN_RUN = Permission.SCAN_RUN
SCAN_CANCEL = Permission.SCAN_CANCEL

SCAN_PERMISSIONS = frozenset(
    {
        SCAN_READ,
        SCAN_CREATE,
        SCAN_RUN,
        SCAN_CANCEL,
    }
)
