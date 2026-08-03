"""Deterministic risk scoring — no AI, rule-based points and grades."""

from app.findings.enums import FindingSeverity

SEVERITY_POINTS: dict[FindingSeverity, float] = {
    FindingSeverity.INFO: 0.0,
    FindingSeverity.LOW: 5.0,
    FindingSeverity.MEDIUM: 15.0,
    FindingSeverity.HIGH: 30.0,
    FindingSeverity.CRITICAL: 50.0,
}

SEVERITY_SORT_ORDER: dict[FindingSeverity, int] = {
    FindingSeverity.CRITICAL: 0,
    FindingSeverity.HIGH: 1,
    FindingSeverity.MEDIUM: 2,
    FindingSeverity.LOW: 3,
    FindingSeverity.INFO: 4,
}


def points_for_severity(severity: FindingSeverity) -> float:
    return SEVERITY_POINTS.get(severity, 0.0)


def total_risk(points: list[float]) -> float:
    return sum(points)


def security_score(total_risk_points: float) -> float:
    return max(0.0, 100.0 - total_risk_points)


def grade_from_security_score(score: float) -> str:
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def risk_level_from_security_score(score: float) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Poor"
    return "Critical"


def compute_trend(current: float, previous: float | None) -> str:
    if previous is None:
        return "stable"
    delta = current - previous
    if delta > 1:
        return "improving"
    if delta < -1:
        return "declining"
    return "stable"
