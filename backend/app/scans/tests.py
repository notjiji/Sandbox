"""Scans feature tests — expand as the module grows."""


def test_scans_module_imports() -> None:
    from app.scans.enums import ScanStatus, ScanType
    from app.scans.models import Scan
    from app.scans.services import scan_service

    assert Scan.__tablename__ == "scans"
    assert ScanType.FULL.value == "full"
    assert ScanStatus.PENDING.value == "pending"
    assert callable(scan_service.list_project_scans)
