"""Backward-compatible re-exports — prefer app.plugins.base.output."""

from app.plugins.base.output import (
    PluginFinding,
    PluginFindingStatus,
    PluginOutput,
    PluginOutputStatus,
    report_finding,
)

__all__ = [
    "PluginFinding",
    "PluginFindingStatus",
    "PluginOutput",
    "PluginOutputStatus",
    "report_finding",
]
