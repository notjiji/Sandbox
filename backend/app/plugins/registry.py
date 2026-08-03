from app.plugins.base import ScannerPlugin
from app.scans.enums import ScanType


class PluginRegistry:
    """Central registry for scanner plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, ScannerPlugin] = {}

    def register(self, plugin: ScannerPlugin) -> None:
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> ScannerPlugin | None:
        return self._plugins.get(name)

    def all(self) -> list[ScannerPlugin]:
        return sorted(self._plugins.values(), key=lambda plugin: plugin.name)

    def list_names(self) -> list[str]:
        return sorted(self._plugins.keys())

    def get_enabled_plugins(
        self,
        *,
        scan_type: ScanType | None = None,
        asset_type: str | None = None,
    ) -> list[ScannerPlugin]:
        """Return enabled plugins, optionally filtered by scan and asset type."""
        plugins = [plugin for plugin in self.all() if plugin.enabled]
        if scan_type is not None:
            plugins = [plugin for plugin in plugins if plugin.supports_scan_type(scan_type)]
        if asset_type is not None:
            plugins = [plugin for plugin in plugins if plugin.supports_asset(asset_type)]
        return plugins

    def get_disabled_plugins(self) -> list[ScannerPlugin]:
        return [plugin for plugin in self.all() if not plugin.enabled]


registry = PluginRegistry()
