"""Standard plugin output and finding schemas — every plugin returns this shape."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import Field

from app.findings.enums import FindingSeverity
from app.shared.schemas.base import BaseSchema


class PluginOutputStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class PluginFindingStatus(str, Enum):
    FAILED = "failed"
    PASSED = "passed"
    WARNING = "warning"


class PluginFinding(BaseSchema):
    """Normalized finding every plugin returns — Risk Engine assigns score and severity."""

    plugin: str
    code: str = Field(description="Stable finding code, e.g. HTTP_NO_CSP")
    title: str | None = None
    status: PluginFindingStatus = PluginFindingStatus.FAILED
    evidence: str | None = None
    severity: FindingSeverity | None = Field(
        default=None,
        description="Optional hint only — Risk Engine applies rule severity",
    )
    raw_data: dict = Field(default_factory=dict)
    detected_at: datetime | None = None


class PluginOutput(BaseSchema):
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


def report_finding(
    *,
    plugin: str,
    code: str,
    title: str | None = None,
    status: PluginFindingStatus = PluginFindingStatus.FAILED,
    evidence: str | None = None,
    severity: FindingSeverity | None = None,
    raw_data: dict | None = None,
    detected_at: datetime | None = None,
) -> PluginFinding:
    return PluginFinding(
        plugin=plugin,
        code=code,
        title=title,
        status=status,
        evidence=evidence,
        severity=severity,
        raw_data=raw_data or {},
        detected_at=detected_at or datetime.now(UTC),
    )
