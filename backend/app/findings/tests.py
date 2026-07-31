"""Findings feature tests — expand as the module grows."""


def test_findings_module_imports() -> None:
    from app.findings.enums import FindingSeverity, FindingStatus
    from app.findings.models import Finding
    from app.findings.services import finding_service

    assert Finding.__tablename__ == "findings"
    assert FindingSeverity.CRITICAL.value == "critical"
    assert FindingStatus.OPEN.value == "open"
    assert callable(finding_service.list_project_findings)
