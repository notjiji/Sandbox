"""Scan engine execution types."""

from dataclasses import dataclass, field

from app.plugins.base.plugin import ScanTarget
from app.plugins.base.contracts import ScanFinding, ScanResult, ScanResultStatus
from app.scans.enums import PluginRunStatus


@dataclass
class PluginExecutionRecord:
    plugin_name: str
    target: ScanTarget
    status: PluginRunStatus
    output: ScanResult | None = None
    error_message: str | None = None
    normalized_findings: list[ScanFinding] = field(default_factory=list)
    duration: float = 0.0


@dataclass
class CombinedScanResults:
    findings: list[ScanFinding] = field(default_factory=list)
    plugin_records: list[PluginExecutionRecord] = field(default_factory=list)

    @property
    def total_findings(self) -> int:
        return len(self.findings)

    @property
    def completed_plugins(self) -> int:
        return sum(1 for record in self.plugin_records if record.status == PluginRunStatus.COMPLETED)

    @property
    def failed_plugins(self) -> int:
        return sum(1 for record in self.plugin_records if record.status == PluginRunStatus.FAILED)
