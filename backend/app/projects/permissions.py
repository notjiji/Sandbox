"""Project feature permissions — re-exported from core RBAC registry."""

from app.core.permissions import Permission

PROJECT_READ = Permission.PROJECT_READ
PROJECT_CREATE = Permission.PROJECT_CREATE
PROJECT_UPDATE = Permission.PROJECT_UPDATE
PROJECT_DELETE = Permission.PROJECT_DELETE

PROJECT_PERMISSIONS = frozenset(
    {
        PROJECT_READ,
        PROJECT_CREATE,
        PROJECT_UPDATE,
        PROJECT_DELETE,
    }
)
