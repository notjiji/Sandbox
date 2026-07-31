"""Members feature tests — expand as the module grows."""


def test_members_module_imports() -> None:
    from app.members.enums import MemberStatus, OrganizationRole
    from app.members.models import OrganizationMember
    from app.members.services import invite_service, member_service

    assert OrganizationMember.__tablename__ == "organization_members"
    assert OrganizationRole.OWNER.value == "owner"
    assert MemberStatus.ACTIVE.value == "active"
    assert callable(member_service.list_current_organization_members)
    assert callable(invite_service.invite_member)
