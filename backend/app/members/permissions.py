"""Member feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

MEMBER_READ = Permission.MEMBER_READ
MEMBER_INVITE = Permission.MEMBER_INVITE
MEMBER_UPDATE = Permission.MEMBER_UPDATE
MEMBER_REMOVE = Permission.MEMBER_REMOVE
MEMBER_TRANSFER_OWNERSHIP = Permission.MEMBER_TRANSFER_OWNERSHIP

MEMBER_PERMISSIONS = frozenset(
    {
        MEMBER_READ,
        MEMBER_INVITE,
        MEMBER_UPDATE,
        MEMBER_REMOVE,
        MEMBER_TRANSFER_OWNERSHIP,
    }
)
