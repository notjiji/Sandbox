"""Scans feature tests — expand as the module grows."""


def test_scans_module_imports() -> None:
    from app.scans.enums import ScanStatus, ScanType
    from app.scans.models import Scan
    from app.scans.services import scan_service

    assert Scan.__tablename__ == "scans"
    assert ScanType.FULL.value == "full"
    assert ScanStatus.PENDING.value == "pending"
    assert callable(scan_service.list_asset_scans)
    assert callable(scan_service.run_asset_scan)


def test_risk_calculator_scores_findings() -> None:
    from app.risk.calculator import RiskCalculator

    calculator = RiskCalculator()
    score = calculator.score_findings(
        [{"severity": "critical"}, {"severity": "low"}, {"severity": "info"}]
    )
    assert score == 11.25
