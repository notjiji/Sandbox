"""Scanner plugin contracts for independent Python packages."""

from datetime import UTC, datetime
from enum import Enum
from typing import Protocol

from scanner_sdk.exceptions import ScannerError


class ScanResultStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


class FindingCheckStatus(str, Enum):
    FAILED = "failed"
    PASSED = "passed"
    WARNING = "warning"


class ScanTarget:
    """Normalized asset passed to scanner plugins."""

    def __init__(self, *, asset_id: str, identifier: str, asset_type: str) -> None:
        self.asset_id = asset_id
        self.identifier = identifier
        self.asset_type = asset_type


class ScanOptions:
    def __init__(self, *, timeout: float = 30.0, retries: int = 0, parallel: bool = False) -> None:
        self.timeout = timeout
        self.retries = retries
        self.parallel = parallel


class ScanFinding:
    """Normalized finding returned by every scanner plugin."""

    def __init__(
        self,
        *,
        plugin: str,
        rule_id: str,
        asset_id: str,
        title: str,
        description: str | None = None,
        severity: str | None = None,
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
    ) -> None:
        self.plugin = plugin
        self.rule_id = rule_id
        self.asset_id = asset_id
        self.title = title
        self.description = description
        self.severity = severity
        self.category = category
        self.evidence = evidence
        self.recommendation = recommendation
        self.reference_links = reference_links or []
        self.cvss = cvss
        self.cwe = cwe
        self.cve = cve
        self.confidence = confidence
        self.status = status
        self.detected_at = detected_at or datetime.now(UTC)

    def to_dict(self) -> dict:
        return {
            "plugin": self.plugin,
            "rule_id": self.rule_id,
            "asset_id": self.asset_id,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
            "reference_links": self.reference_links,
            "cvss": self.cvss,
            "cwe": self.cwe,
            "cve": self.cve,
            "confidence": self.confidence,
            "status": self.status.value,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
        }


class ScanResult:
    """Standard output every scanner plugin must return."""

    def __init__(
        self,
        *,
        plugin: str,
        version: str,
        started_at: datetime,
        finished_at: datetime,
        status: ScanResultStatus,
        metadata: dict | None = None,
        findings: list[ScanFinding] | None = None,
        error: str | None = None,
    ) -> None:
        self.plugin = plugin
        self.version = version
        self.started_at = started_at
        self.finished_at = finished_at
        self.status = status
        self.metadata = metadata or {}
        self.findings = findings or []
        self.error = error

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
        error: str,
        finished_at: datetime | None = None,
        metadata: dict | None = None,
    ) -> "ScanResult":
        return cls(
            plugin=plugin,
            version=version,
            started_at=started_at,
            finished_at=finished_at or datetime.now(UTC),
            status=ScanResultStatus.FAILED,
            metadata=metadata or {"error": error},
            error=error,
        )

    def to_dict(self) -> dict:
        return {
            "plugin": self.plugin,
            "version": self.version,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat(),
            "status": self.status.value,
            "metadata": self.metadata,
            "findings": [finding.to_dict() for finding in self.findings],
            "error": self.error,
        }


class ScannerPlugin(Protocol):
    id: str
    name: str
    version: str
    supported_asset_types: list[str]

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        """Execute a scan and return the standard ScanResult structure."""


__all__ = [
    "FindingCheckStatus",
    "ScanFinding",
    "ScanOptions",
    "ScanResult",
    "ScanResultStatus",
    "ScanTarget",
    "ScannerError",
    "ScannerPlugin",
]
