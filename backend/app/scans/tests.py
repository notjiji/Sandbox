"""Scans feature tests — expand as the module grows."""


def test_scans_module_imports() -> None:
    from app.scans.enums import ScanStatus, ScanType
    from app.scans.models import Scan
    from app.scans.profiles import SCAN_PROFILE_PLUGINS
    from app.scans.services import scan_service

    assert Scan.__tablename__ == "scans"
    assert ScanType.FULL.value == "full"
    assert ScanType.CUSTOM.value == "custom"
    assert ScanStatus.QUEUED.value == "queued"
    assert ScanStatus.PENDING.value == "pending"
    assert SCAN_PROFILE_PLUGINS[ScanType.QUICK] == ["http_headers", "ssl", "dns", "cookies"]
    assert "robots" in SCAN_PROFILE_PLUGINS[ScanType.FULL]
    assert "tls" in SCAN_PROFILE_PLUGINS[ScanType.FULL]
    assert callable(scan_service.list_asset_scans)
    assert callable(scan_service.run_asset_scan)
    assert callable(scan_service.list_scan_profile_options)


def test_risk_calculator_scores_findings() -> None:
    from app.risk.calculator import RiskCalculator

    calculator = RiskCalculator()
    score = calculator.score_findings(
        [{"risk_score": 10}, {"risk_score": 25}, {"risk_score": 5}]
    )
    assert score == 40.0
