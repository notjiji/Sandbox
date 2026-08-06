"""Backward-compatible aliases for the standard scanner contracts."""

from enum import Enum

from app.plugins.base.contracts import (
    FindingCheckStatus,
    ScanFinding,
    ScanOptions,
    ScanResult,
    ScanResultStatus,
    scan_finding,
)


class PluginOutputStatus(str, Enum):
    """Legacy scan result status — maps to ScanResultStatus."""

    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

    @classmethod
    def from_scan_result(cls, status: ScanResultStatus) -> "PluginOutputStatus":
        if status == ScanResultStatus.SUCCESS:
            return cls.COMPLETED
        if status == ScanResultStatus.SKIPPED:
            return cls.SKIPPED
        return cls.FAILED


PluginFindingStatus = FindingCheckStatus
PluginFinding = ScanFinding
PluginOutput = ScanResult
report_finding = scan_finding

__all__ = [
    "FindingCheckStatus",
    "PluginFinding",
    "PluginFindingStatus",
    "PluginOutput",
    "PluginOutputStatus",
    "ScanFinding",
    "ScanOptions",
    "ScanResult",
    "ScanResultStatus",
    "report_finding",
    "scan_finding",
]
