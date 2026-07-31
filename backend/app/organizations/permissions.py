"""Organization feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

ORG_READ = Permission.ORG_READ
ORG_UPDATE = Permission.ORG_UPDATE
ORG_DELETE = Permission.ORG_DELETE

ORGANIZATION_PERMISSIONS = frozenset(
    {
        ORG_READ,
        ORG_UPDATE,
        ORG_DELETE,
    }
)
