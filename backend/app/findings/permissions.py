"""Finding feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

FINDING_READ = Permission.FINDING_READ
FINDING_UPDATE = Permission.FINDING_UPDATE

FINDING_PERMISSIONS = frozenset(
    {
        FINDING_READ,
        FINDING_UPDATE,
    }
)
