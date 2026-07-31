"""Asset feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

ASSET_READ = Permission.ASSET_READ
ASSET_CREATE = Permission.ASSET_CREATE
ASSET_UPDATE = Permission.ASSET_UPDATE
ASSET_DELETE = Permission.ASSET_DELETE

ASSET_PERMISSIONS = frozenset(
    {
        ASSET_READ,
        ASSET_CREATE,
        ASSET_UPDATE,
        ASSET_DELETE,
    }
)
