"""Domain-level risk calculator — delegates to rule-based finding scores."""

from app.assets.enums import CRITICALITY_RISK_MULTIPLIERS, AssetCriticality


class RiskCalculator:
    def score_findings(self, findings: list[dict]) -> float:
        """Score findings using pre-calculated risk_score values from the Risk Engine."""
        total = 0.0
        for finding in findings:
            base_score = float(finding.get("risk_score", 0.0))
            criticality = finding.get("criticality")
            multiplier = 1.0
            if criticality:
                try:
                    multiplier = CRITICALITY_RISK_MULTIPLIERS[AssetCriticality(criticality)]
                except ValueError:
                    multiplier = 1.0
            total += base_score * multiplier
        return total
