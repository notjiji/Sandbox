"""Domain-level risk calculator (uses core.risk_engine weights)."""

from app.assets.enums import CRITICALITY_RISK_MULTIPLIERS, AssetCriticality
from app.core.risk_engine.weights import SEVERITY_WEIGHTS

DEFAULT_WEIGHTS = SEVERITY_WEIGHTS


class RiskCalculator:
    def score_findings(self, findings: list[dict]) -> float:
        total = 0.0
        for finding in findings:
            severity = str(finding.get("severity", "info")).lower()
            base_score = DEFAULT_WEIGHTS.get(severity, 0.0)
            criticality = finding.get("criticality")
            multiplier = 1.0
            if criticality:
                try:
                    multiplier = CRITICALITY_RISK_MULTIPLIERS[AssetCriticality(criticality)]
                except ValueError:
                    multiplier = 1.0
            total += base_score * multiplier
        return total
