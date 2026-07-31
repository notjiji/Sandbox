"""Risk scoring engine — consumes normalized findings, produces risk scores."""

from app.core.risk_engine.calculator import RiskCalculator

__all__ = ["RiskCalculator"]
