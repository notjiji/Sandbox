"""Report feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

REPORT_READ = Permission.REPORT_READ
REPORT_GENERATE = Permission.REPORT_GENERATE
REPORT_DELETE = Permission.REPORT_DELETE

REPORT_PERMISSIONS = frozenset(
    {
        REPORT_READ,
        REPORT_GENERATE,
        REPORT_DELETE,
    }
)
