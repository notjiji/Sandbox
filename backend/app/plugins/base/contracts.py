"""Standard scanner contracts — every plugin implements and returns these shapes."""

from datetime import UTC, datetime
from enum import Enum

from pydantic import AliasChoices, Field

from app.findings.enums import FindingSeverity
from app.shared.schemas.base import BaseSchema


class ScanResultStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class FindingCheckStatus(str, Enum):
    FAILED = "failed"
    PASSED = "passed"
    WARNING = "warning"


class ScanOptions(BaseSchema):
    timeout: float = Field(default=30.0, ge=0.0)
    retries: int = Field(default=0, ge=0)
    parallel: bool = False


class ScanFinding(BaseSchema):
    """Normalized finding returned by every scanner plugin."""

    plugin: str
    rule_id: str = Field(
        description="Stable rule identifier, e.g. SSL_TLS10_ENABLED",
        validation_alias=AliasChoices("rule_id", "code"),
    )
    asset_id: str
    title: str
    description: str | None = None
    severity: FindingSeverity | None = Field(
        default=None,
        description="Optional hint — Risk Engine may override from rules",
    )
    category: str | None = None
    evidence: str | None = None
    recommendation: str | None = None
    reference_links: list[str] = Field(default_factory=list)
    cvss: float | None = None
    cwe: str | None = None
    cve: str | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    status: FindingCheckStatus = FindingCheckStatus.FAILED
    detected_at: datetime | None = None
    resolved_at: datetime | None = None
    raw_data: dict = Field(default_factory=dict)


class ScanResult(BaseSchema):
    """Standard output every scanner plugin must return."""

    plugin: str
    version: str
    started_at: datetime
    finished_at: datetime
    status: ScanResultStatus
    metadata: dict = Field(default_factory=dict)
    findings: list[ScanFinding] = Field(default_factory=list)
    error: str | None = None

    @property
    def duration(self) -> float:
        return max((self.finished_at - self.started_at).total_seconds(), 0.0)

    @classmethod
    def success(
        cls,
        *,
        plugin: str,
        version: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        findings: list[ScanFinding] | None = None,
        metadata: dict | None = None,
    ) -> "ScanResult":
        return cls(
            plugin=plugin,
            version=version,
            started_at=started_at,
            finished_at=finished_at or datetime.now(UTC),
            status=ScanResultStatus.SUCCESS,
            findings=findings or [],
            metadata=metadata or {},
        )

    @classmethod
    def failure(
        cls,
        *,
        plugin: str,
        version: str,
        started_at: datetime,
        finished_at: datetime | None = None,
        error: str,
        metadata: dict | None = None,
    ) -> "ScanResult":
        return cls(
            plugin=plugin,
            version=version,
            started_at=started_at,
            finished_at=finished_at or datetime.now(UTC),
            status=ScanResultStatus.FAILED,
            findings=[],
            metadata=metadata or {"error": error},
            error=error,
        )


def scan_finding(
    *,
    plugin: str,
    rule_id: str | None = None,
    code: str | None = None,
    asset_id: str,
    title: str,
    description: str | None = None,
    severity: FindingSeverity | None = None,
    category: str | None = None,
    evidence: str | None = None,
    recommendation: str | None = None,
    reference_links: list[str] | None = None,
    cvss: float | None = None,
    cwe: str | None = None,
    cve: str | None = None,
    confidence: float | None = None,
    status: FindingCheckStatus = FindingCheckStatus.FAILED,
    detected_at: datetime | None = None,
    raw_data: dict | None = None,
) -> ScanFinding:
    resolved_rule_id = rule_id or code
    if not resolved_rule_id:
        raise ValueError("rule_id is required")
    return ScanFinding(
        plugin=plugin,
        rule_id=resolved_rule_id,
        asset_id=asset_id,
        title=title,
        description=description,
        severity=severity,
        category=category,
        evidence=evidence,
        recommendation=recommendation,
        reference_links=reference_links or [],
        cvss=cvss,
        cwe=cwe,
        cve=cve,
        confidence=confidence,
        status=status,
        detected_at=detected_at or datetime.now(UTC),
        raw_data=raw_data or {},
    )
