"""Pydantic models for the AI service layer."""

from __future__ import annotations

import uuid
from enum import Enum
from typing import Any, Literal

from app.shared.schemas.base import BaseSchema


class AICapability(str, Enum):
    EXPLAIN_FINDING = "explain_finding"
    EXPLAIN_RISK_SCORE = "explain_risk_score"
    REMEDIATION = "remediation"
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_SUMMARY = "technical_summary"
    COMPARE_SCANS = "compare_scans"
    ASSET_SUMMARY = "asset_summary"
    ORGANIZATION_OVERVIEW = "organization_overview"
    GENERAL = "general"


class AIChatRequest(BaseSchema):
    message: str
    capability: AICapability = AICapability.GENERAL
    conversation_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    asset_id: uuid.UUID | None = None
    scan_id: uuid.UUID | None = None
    finding_id: uuid.UUID | None = None
    finding_code: str | None = None
    audience: Literal["executive", "technical"] | None = None


class AIResponsePayload(BaseSchema):
    answer: str
    summary: str | None = None
    references: list[str] = []
    related_findings: list[str] = []
    confidence: Literal["high", "medium", "low"] = "high"
    disclaimer: str | None = None


class AIChatResponse(BaseSchema):
    conversation_id: uuid.UUID
    capability: AICapability
    response: AIResponsePayload
    context_keys: list[str] = []
    model: str | None = None


class FindingContext(BaseSchema):
    id: str
    plugin: str | None = None
    finding_code: str | None = None
    severity: str
    title: str
    description: str | None = None
    evidence: str | None = None
    recommendation: str | None = None
    risk_score: float = 0.0
    status: str | None = None
    references: list[str] = []


class ScanContextSnapshot(BaseSchema):
    scan_id: str
    scan_date: str | None = None
    scan_type: str | None = None
    status: str | None = None
    findings_count: int = 0
    risk_score: float | None = None


class AssetContextSnapshot(BaseSchema):
    asset_id: str
    name: str
    identifier: str
    asset_type: str | None = None
    latest_scan: ScanContextSnapshot | None = None
    risk_score: float | None = None
    open_findings_count: int = 0


class AIContextBundle(BaseSchema):
    """Structured context sent to the LLM — never raw database rows."""

    organization_id: str
    capability: str
    asset: AssetContextSnapshot | None = None
    scan: ScanContextSnapshot | None = None
    risk_score: float | None = None
    findings: list[FindingContext] = []
    scan_comparison: dict[str, Any] | None = None
    organization_summary: dict[str, Any] | None = None
    metadata: dict[str, Any] = {}
