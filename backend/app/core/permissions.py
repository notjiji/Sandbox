import enum


class Permission(str, enum.Enum):
    ORG_READ = "org:read"
    ORG_UPDATE = "org:update"
    ORG_DELETE = "org:delete"
    ORG_BILLING = "org:billing"

    MEMBER_READ = "member:read"
    MEMBER_INVITE = "member:invite"
    MEMBER_UPDATE = "member:update"
    MEMBER_REMOVE = "member:remove"
    MEMBER_TRANSFER_OWNERSHIP = "member:transfer_ownership"

    PROJECT_READ = "project:read"
    PROJECT_CREATE = "project:create"
    PROJECT_UPDATE = "project:update"
    PROJECT_DELETE = "project:delete"

    ASSET_READ = "asset:read"
    ASSET_CREATE = "asset:create"
    ASSET_UPDATE = "asset:update"
    ASSET_DELETE = "asset:delete"

    SCAN_READ = "scan:read"
    SCAN_CREATE = "scan:create"
    SCAN_RUN = "scan:run"
    SCAN_CANCEL = "scan:cancel"

    FINDING_READ = "finding:read"
    FINDING_REVIEW = "finding:review"
    FINDING_UPDATE = "finding:update"

    REPORT_READ = "report:read"
    REPORT_GENERATE = "report:generate"
    REPORT_DELETE = "report:delete"

    DASHBOARD_VIEW = "dashboard:view"


ALL_PERMISSIONS = frozenset(Permission)

OWNER_PERMISSIONS = ALL_PERMISSIONS

ADMIN_PERMISSIONS = ALL_PERMISSIONS - {
    Permission.ORG_DELETE,
    Permission.ORG_BILLING,
    Permission.MEMBER_TRANSFER_OWNERSHIP,
}

SECURITY_ANALYST_PERMISSIONS = frozenset(
    {
        Permission.ORG_READ,
        Permission.MEMBER_READ,
        Permission.PROJECT_READ,
        Permission.PROJECT_CREATE,
        Permission.PROJECT_UPDATE,
        Permission.ASSET_READ,
        Permission.ASSET_CREATE,
        Permission.ASSET_UPDATE,
        Permission.SCAN_READ,
        Permission.SCAN_CREATE,
        Permission.SCAN_RUN,
        Permission.SCAN_CANCEL,
        Permission.FINDING_READ,
        Permission.FINDING_REVIEW,
        Permission.FINDING_UPDATE,
        Permission.REPORT_READ,
        Permission.REPORT_GENERATE,
        Permission.DASHBOARD_VIEW,
    }
)

MANAGER_PERMISSIONS = frozenset(
    {
        Permission.ORG_READ,
        Permission.MEMBER_READ,
        Permission.PROJECT_READ,
        Permission.ASSET_READ,
        Permission.SCAN_READ,
        Permission.FINDING_READ,
        Permission.REPORT_READ,
        Permission.DASHBOARD_VIEW,
    }
)

VIEWER_PERMISSIONS = frozenset(
    {
        Permission.ORG_READ,
        Permission.PROJECT_READ,
        Permission.ASSET_READ,
        Permission.SCAN_READ,
        Permission.FINDING_READ,
        Permission.REPORT_READ,
    }
)
