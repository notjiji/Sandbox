from app.core.permissions import Permission
from app.core.rbac import ROLE_DESCRIPTIONS, get_permissions_for_role
from app.members.enums import OrganizationRole
from app.schemas.base import BaseSchema


class RoleInfo(BaseSchema):
    role: OrganizationRole
    description: str
    permissions: list[str]


class RolesListResponse(BaseSchema):
    roles: list[RoleInfo]


def build_roles_list_response() -> RolesListResponse:
    roles = [
        RoleInfo(
            role=role,
            description=ROLE_DESCRIPTIONS[role],
            permissions=sorted(p.value for p in get_permissions_for_role(role)),
        )
        for role in OrganizationRole
    ]
    return RolesListResponse(roles=roles)
