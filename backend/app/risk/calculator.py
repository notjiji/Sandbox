"""Domain-level risk calculator (uses core.risk_engine weights)."""

from app.core.risk_engine.weights import SEVERITY_WEIGHTS

DEFAULT_WEIGHTS = SEVERITY_WEIGHTS


class RiskCalculator:
    def score_findings(self, findings: list[dict]) -> float:
        total = 0.0
        for finding in findings:
            severity = str(finding.get("severity", "info")).lower()
            total += DEFAULT_WEIGHTS.get(severity, 0.0)
        return total
