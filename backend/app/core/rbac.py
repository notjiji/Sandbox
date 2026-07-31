from app.core.permissions import (
    ADMIN_PERMISSIONS,
    MANAGER_PERMISSIONS,
    OWNER_PERMISSIONS,
    SECURITY_ANALYST_PERMISSIONS,
    VIEWER_PERMISSIONS,
    Permission,
)
from app.members.enums import OrganizationRole

ROLE_PERMISSIONS: dict[OrganizationRole, frozenset[Permission]] = {
    OrganizationRole.OWNER: OWNER_PERMISSIONS,
    OrganizationRole.ADMIN: ADMIN_PERMISSIONS,
    OrganizationRole.SECURITY_ANALYST: SECURITY_ANALYST_PERMISSIONS,
    OrganizationRole.MANAGER: MANAGER_PERMISSIONS,
    OrganizationRole.VIEWER: VIEWER_PERMISSIONS,
}

ROLE_DESCRIPTIONS: dict[OrganizationRole, str] = {
    OrganizationRole.OWNER: "Full control of the organization, billing, member management, and deletion",
    OrganizationRole.ADMIN: "Manage assets, scans, reports, and users (except ownership)",
    OrganizationRole.SECURITY_ANALYST: "Create assets, run scans, review findings, and generate reports",
    OrganizationRole.MANAGER: "View dashboards, findings, and reports",
    OrganizationRole.VIEWER: "Read-only access",
}


def get_permissions_for_role(role: OrganizationRole) -> frozenset[Permission]:
    return ROLE_PERMISSIONS[role]


def has_permission(role: OrganizationRole, permission: Permission) -> bool:
    return permission in ROLE_PERMISSIONS[role]


def has_any_permission(role: OrganizationRole, *permissions: Permission) -> bool:
    role_permissions = ROLE_PERMISSIONS[role]
    return any(permission in role_permissions for permission in permissions)


def has_all_permissions(role: OrganizationRole, *permissions: Permission) -> bool:
    role_permissions = ROLE_PERMISSIONS[role]
    return all(permission in role_permissions for permission in permissions)
