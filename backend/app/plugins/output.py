"""Standard plugin output and finding schemas — every plugin returns this shape."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import Field

from app.findings.enums import FindingSeverity
from app.schemas.base import BaseSchema


class PluginOutputStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PluginFinding(BaseSchema):
    """Normalized finding every plugin must produce before returning."""

    plugin: str
    title: str
    description: str | None = None
    severity: FindingSeverity = FindingSeverity.INFO
    evidence: str | None = None
    recommendation: str | None = None
    references: list[str] = Field(default_factory=list)
    raw_data: dict = Field(default_factory=dict)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    detected_at: datetime | None = None


class PluginOutput(BaseSchema):
    """Exact structure returned by every scanner plugin — no exceptions."""

    plugin: str
    status: PluginOutputStatus
    duration: float = Field(ge=0.0)
    findings: list[PluginFinding] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    error: str | None = None

    @classmethod
    def failed(
        cls,
        *,
        plugin: str,
        duration: float = 0.0,
        error: str,
        metadata: dict | None = None,
    ) -> "PluginOutput":
        return cls(
            plugin=plugin,
            status=PluginOutputStatus.FAILED,
            duration=duration,
            findings=[],
            metadata=metadata or {"error": error},
            error=error,
        )

    @classmethod
    def completed(
        cls,
        *,
        plugin: str,
        duration: float,
        findings: list[PluginFinding] | None = None,
        metadata: dict | None = None,
    ) -> "PluginOutput":
        return cls(
            plugin=plugin,
            status=PluginOutputStatus.COMPLETED,
            duration=duration,
            findings=findings or [],
            metadata=metadata or {},
        )


def make_finding(
    *,
    plugin: str,
    title: str,
    severity: FindingSeverity = FindingSeverity.INFO,
    description: str | None = None,
    evidence: str | None = None,
    recommendation: str | None = None,
    references: list[str] | None = None,
    raw_data: dict | None = None,
    confidence: float | None = None,
    detected_at: datetime | None = None,
) -> PluginFinding:
    return PluginFinding(
        plugin=plugin,
        title=title,
        description=description,
        severity=severity,
        evidence=evidence,
        recommendation=recommendation,
        references=references or [],
        raw_data=raw_data or {},
        confidence=confidence,
        detected_at=detected_at or datetime.now(UTC),
    )
