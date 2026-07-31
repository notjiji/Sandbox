import enum


class OrganizationRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    SECURITY_ANALYST = "security_analyst"
    MANAGER = "manager"
    VIEWER = "viewer"


class MemberStatus(str, enum.Enum):
    INVITED = "invited"
    ACTIVE = "active"
    SUSPENDED = "suspended"
