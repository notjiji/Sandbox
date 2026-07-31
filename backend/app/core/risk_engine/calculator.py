"""Calculates project/asset risk from findings using configured weights."""


class RiskCalculator:
    def score(self, *, findings: list[dict]) -> float:
        raise NotImplementedError("Risk scoring not implemented yet")
