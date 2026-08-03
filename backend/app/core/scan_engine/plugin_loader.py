"""Loads scanner plugins from the central registry."""

from dataclasses import dataclass

from app.core.exceptions import ValidationAppError
from app.plugins.base import ScannerPlugin
from app.plugins.builtin import discover_plugins
from app.plugins.registry import registry
from app.scans.profiles import resolve_profile_plugins


@dataclass(frozen=True)
class PluginSelection:
    enabled: list[ScannerPlugin]
    skipped: list[str]


class PluginLoader:
    def ensure_loaded(self) -> None:
        """Discover and register built-in plugins if not already loaded."""
        if registry.list_names():
            return
        discover_plugins(registry)

    def select_for_scan(self, scan) -> PluginSelection:
        """Resolve scan profile plugins from the registry."""
        self.ensure_loaded()
        plugin_names = resolve_profile_plugins(scan.scan_type, scan.selected_plugins)
        enabled, missing = registry.resolve_plugin_names(plugin_names)
        if scan.scan_type.value != "custom" and missing:
            raise ValidationAppError(f"Profile plugin(s) unavailable: {', '.join(missing)}")
        if scan.scan_type.value == "custom" and not enabled:
            raise ValidationAppError("None of the selected plugins are available")
        disabled = [plugin.name for plugin in registry.get_disabled_plugins()]
        return PluginSelection(enabled=enabled, skipped=missing + disabled)
