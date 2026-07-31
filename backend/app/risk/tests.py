def test_risk_module_imports() -> None:
    from app.risk.calculator import RiskCalculator
    from app.risk.service import RiskService

    assert callable(RiskService().calculate_project_risk)
    assert RiskCalculator().score_findings([]) == 0.0
