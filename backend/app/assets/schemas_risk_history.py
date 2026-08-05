from datetime import datetime

from pydantic import Field

from app.risk.schemas import AssetRiskResponse
from app.shared.schemas.base import BaseSchema


class RiskHistoryPoint(BaseSchema):
    id: str
    date: datetime
    security_score: float
    total_risk: float
    grade: str
    scan_id: str | None = None
    score_delta: float | None = None
    total_risk_delta: float | None = None


class RiskChangeExplanation(BaseSchema):
    delta: float = Field(description="Risk points change; positive = risk increased")
    title: str
    kind: str = Field(description="new | resolved")
    finding_id: str | None = None
    severity: str | None = None


class RiskHistoryChange(BaseSchema):
    from_score: float
    to_score: float
    from_date: datetime
    to_date: datetime
    score_delta: float
    total_risk_delta: float
    explanations: list[RiskChangeExplanation] = Field(default_factory=list)


class AssetRiskHistoryResponse(BaseSchema):
    current: AssetRiskResponse
    trend: list[RiskHistoryPoint] = Field(default_factory=list)
    latest_change: RiskHistoryChange | None = None
    changes: list[RiskHistoryChange] = Field(default_factory=list)
