"""Reports feature tests — expand as the module grows."""


def test_reports_module_imports() -> None:
    from app.reports.enums import ReportStatus
    from app.reports.models import Report
    from app.reports.services import report_service

    assert Report.__tablename__ == "reports"
    assert ReportStatus.DRAFT.value == "draft"
    assert callable(report_service.list_project_reports)
