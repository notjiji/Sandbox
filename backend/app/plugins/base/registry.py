from app.plugins.base.plugin import ScannerPlugin
from app.scans.enums import ScanType


class PluginRegistry:
    """Stores and looks up registered scanner plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, ScannerPlugin] = {}

    def register(self, plugin: ScannerPlugin) -> None:
        self._plugins[plugin.id] = plugin

    def get(self, name: str) -> ScannerPlugin | None:
        return self._plugins.get(name)

    def all(self) -> list[ScannerPlugin]:
        return sorted(self._plugins.values(), key=lambda plugin: plugin.id)

    def list_names(self) -> list[str]:
        return sorted(self._plugins.keys())

    def get_enabled_plugins(
        self,
        *,
        scan_type: ScanType | None = None,
        asset_type: str | None = None,
        plugin_names: list[str] | None = None,
    ) -> list[ScannerPlugin]:
        if plugin_names is not None:
            plugins = [
                plugin
                for name in plugin_names
                if (plugin := self.get(name)) is not None and plugin.config.enabled
            ]
        else:
            plugins = [plugin for plugin in self.all() if plugin.config.enabled]
            if scan_type is not None:
                plugins = [plugin for plugin in plugins if plugin.supports_scan_type(scan_type)]
        if asset_type is not None:
            plugins = [plugin for plugin in plugins if plugin.supports_asset(asset_type)]
        return plugins

    def resolve_plugin_names(self, plugin_names: list[str]) -> tuple[list[ScannerPlugin], list[str]]:
        found: list[ScannerPlugin] = []
        missing: list[str] = []
        for name in plugin_names:
            plugin = self.get(name)
            if plugin is None or not plugin.config.enabled:
                missing.append(name)
            else:
                found.append(plugin)
        return found, missing

    def get_disabled_plugins(self) -> list[ScannerPlugin]:
        return [plugin for plugin in self.all() if not plugin.config.enabled]

    def get_plugin_configs(self) -> list[dict]:
        return [
            {
                "id": plugin.id,
                "name": plugin.name,
                "description": plugin.name,
                "version": plugin.version,
                **plugin.config.to_dict(),
                "supported_asset_types": plugin.supported_asset_types,
                "supported_assets": plugin.supported_asset_types,
                "supported_scan_types": plugin.supported_scan_types,
            }
            for plugin in self.all()
        ]


registry = PluginRegistry()
