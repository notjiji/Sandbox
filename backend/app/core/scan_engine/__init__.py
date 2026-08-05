"""Scan engine infrastructure — orchestrates plugin execution outside business domain."""

from app.assets.adapter import AssetAdapter, asset_adapter
from app.core.scan_engine.dispatcher import ScanDispatcher
from app.core.scan_engine.normalizer import ScanNormalizer
from app.core.scan_engine.orchestrator import ScanOrchestrator, scan_orchestrator
from app.core.scan_engine.result_combiner import combine_normalized_findings, resolve_scan_status
from app.core.scan_engine.scheduler import ScanScheduler
from app.core.scan_engine.types import CombinedScanResults, PluginExecutionRecord
from app.plugins.base.loader import PluginLoader, PluginSelection, plugin_loader

__all__ = [
    "AssetAdapter",
    "asset_adapter",
    "CombinedScanResults",
    "PluginExecutionRecord",
    "PluginLoader",
    "PluginSelection",
    "ScanDispatcher",
    "ScanNormalizer",
    "ScanOrchestrator",
    "scan_orchestrator",
    "plugin_loader",
    "ScanScheduler",
    "combine_normalized_findings",
    "resolve_scan_status",
]
