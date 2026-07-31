"""Organizations feature tests — expand as the module grows."""


def test_organizations_module_imports() -> None:
    from app.organizations.models import Organization
    from app.organizations.invites import InviteStatus, OrganizationInvite
    from app.organizations.services import organization_service

    assert Organization.__tablename__ == "organizations"
    assert InviteStatus.PENDING.value == "pending"
    assert OrganizationInvite.__tablename__ == "organization_invites"
    assert callable(organization_service.create_user_organization)
