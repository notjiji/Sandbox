"""Projects feature tests — expand as the module grows."""


def test_projects_module_imports() -> None:
    from app.projects.models import Project
    from app.projects.services import project_service

    assert Project.__tablename__ == "projects"
    assert callable(project_service.list_organization_projects)
