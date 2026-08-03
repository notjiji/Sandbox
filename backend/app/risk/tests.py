"""Risk scoring and engine tests."""


def test_security_score_and_grades() -> None:
    from app.core.risk_engine.scoring import (
        grade_from_security_score,
        risk_level_from_security_score,
        security_score,
        total_risk,
    )
    from app.findings.enums import FindingSeverity
    from app.core.risk_engine.scoring import points_for_severity

    assert points_for_severity(FindingSeverity.MEDIUM) == 15
    assert points_for_severity(FindingSeverity.CRITICAL) == 50
    assert total_risk([30, 50, 15, 25]) == 120
    assert security_score(120) == 0
    assert security_score(18) == 82
    assert grade_from_security_score(82) == "B"
    assert grade_from_security_score(95) == "A+"
    assert risk_level_from_security_score(84) == "Good"


def test_trend_detection() -> None:
    from app.core.risk_engine.scoring import compute_trend

    assert compute_trend(79, 72) == "improving"
    assert compute_trend(70, 80) == "declining"
    assert compute_trend(80, 79) == "stable"


def test_risk_calculator_uses_rule_scores() -> None:
    from app.risk.calculator import RiskCalculator

    calculator = RiskCalculator()
    score = calculator.score_findings([{"risk_score": 15}, {"risk_score": 25}, {"risk_score": 30}])
    assert score == 70.0


def test_plugin_finding_normalized_format() -> None:
    from app.plugins.output import PluginFindingStatus, report_finding
    from app.findings.enums import FindingSeverity

    finding = report_finding(
        plugin="http_headers",
        code="HTTP_NO_CSP",
        title="Missing Content Security Policy",
        status=PluginFindingStatus.FAILED,
        evidence="Header not present",
        severity=FindingSeverity.MEDIUM,
    )
    payload = finding.model_dump()
    assert payload["plugin"] == "http_headers"
    assert payload["code"] == "HTTP_NO_CSP"
    assert payload["title"] == "Missing Content Security Policy"
    assert payload["status"] == "failed"
    assert "score" not in payload


def test_unscanned_asset_has_no_score() -> None:
    from app.risk.schemas import unscanned_asset_risk

    payload = unscanned_asset_risk(asset_id="00000000-0000-4000-8000-000000000001").model_dump()
    assert payload["scanned"] is False
    assert payload["score"] is None
    assert payload["grade"] is None
    assert payload["total_risk"] is None


def test_passed_findings_are_not_scored() -> None:
    from unittest.mock import MagicMock

    from app.core.risk_engine.engine import RiskEngine
    from app.plugins.output import PluginFinding, PluginFindingStatus

    engine = RiskEngine()
    finding = PluginFinding(
        plugin="http_headers",
        code="HTTP_NO_CSP",
        status=PluginFindingStatus.PASSED,
    )
    assert engine.resolve_finding(MagicMock(), plugin_finding=finding) is None
