"""Risk engine unit tests."""


def test_risk_calculator_uses_rule_scores() -> None:
    from app.risk.calculator import RiskCalculator

    calculator = RiskCalculator()
    score = calculator.score_findings(
        [
            {"risk_score": 15, "criticality": "medium"},
            {"risk_score": 50, "criticality": "critical"},
        ]
    )
    assert score == 15 * 1.0 + 50 * 4.0


def test_plugin_finding_has_code_not_severity() -> None:
    from app.plugins.output import PluginFinding, PluginFindingStatus, report_finding

    finding = report_finding(
        plugin="http_headers",
        code="HTTP_NO_CSP",
        status=PluginFindingStatus.FAILED,
        evidence="missing header",
    )
    payload = finding.model_dump()
    assert payload["code"] == "HTTP_NO_CSP"
    assert payload["status"] == "failed"
    assert "severity" not in payload
    assert "score" not in payload


def test_passed_findings_are_not_scored() -> None:
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from app.core.risk_engine.engine import RiskEngine
    from app.plugins.output import PluginFinding, PluginFindingStatus

    engine = RiskEngine()
    db = MagicMock()
    finding = PluginFinding(
        plugin="http_headers",
        code="HTTP_NO_CSP",
        status=PluginFindingStatus.PASSED,
    )
    assert engine.resolve_finding(db, plugin_finding=finding) is None


def test_unknown_rule_gets_zero_score() -> None:
    from unittest.mock import MagicMock, patch

    from app.core.risk_engine.engine import RiskEngine
    from app.plugins.output import PluginFinding, PluginFindingStatus

    engine = RiskEngine()
    db = MagicMock()
    finding = PluginFinding(
        plugin="custom",
        code="UNKNOWN_CODE",
        status=PluginFindingStatus.FAILED,
    )
    with patch("app.core.risk_engine.engine.get_rule_for_finding", return_value=None):
        resolved = engine.resolve_finding(db, plugin_finding=finding)
    assert resolved is not None
    assert resolved.risk_score == 0.0
    assert resolved.finding_code == "UNKNOWN_CODE"
