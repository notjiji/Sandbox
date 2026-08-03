"""Scan engine execution types."""

from dataclasses import dataclass, field

from app.plugins.base import ScanTarget
from app.scans.enums import PluginRunStatus


@dataclass
class PluginExecutionRecord:
    plugin_name: str
    target: ScanTarget
    status: PluginRunStatus
    error_message: str | None = None
    raw_findings: list[dict] = field(default_factory=list)
    normalized_findings: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@dataclass
class CombinedScanResults:
    findings: list[dict] = field(default_factory=list)
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
