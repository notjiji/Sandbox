"""Loads scanner plugins from the central registry."""

from dataclasses import dataclass

from app.core.plugin_registry import registry
from app.plugins.base import ScannerPlugin
from app.plugins.builtin import discover_plugins
from app.scans.enums import ScanType


@dataclass(frozen=True)
class PluginSelection:
    enabled: list[ScannerPlugin]
    disabled: list[ScannerPlugin]


class PluginLoader:
    def ensure_loaded(self) -> None:
        """Discover and register built-in plugins if not already loaded."""
        if registry.list_names():
            return
        discover_plugins(registry)

    def select_for_scan(self, scan_type: ScanType) -> PluginSelection:
        """Ask the registry for all plugins applicable to this scan type."""
        self.ensure_loaded()
        enabled = registry.get_enabled_plugins(scan_type=scan_type)
        disabled = registry.get_disabled_plugins()
        return PluginSelection(enabled=enabled, disabled=disabled)
