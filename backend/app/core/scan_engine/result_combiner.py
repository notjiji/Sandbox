"""Resolves final scan status from plugin execution records."""

from app.plugins.output import PluginFinding
from app.scans.enums import PluginRunStatus, ScanStatus
from app.core.scan_engine.types import PluginExecutionRecord


def resolve_scan_status(records: list[PluginExecutionRecord]) -> ScanStatus:
    if not records:
        return ScanStatus.FAILED

    if any(record.status == PluginRunStatus.COMPLETED for record in records):
        return ScanStatus.COMPLETED

    return ScanStatus.FAILED


def combine_normalized_findings(records: list[PluginExecutionRecord]) -> list[PluginFinding]:
    combined: list[PluginFinding] = []
    for record in records:
        combined.extend(record.normalized_findings)
    return combined
