from app.plugins.base import ScannerPlugin


class PluginRegistry:
    """In-memory registry for scanner plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, ScannerPlugin] = {}

    def register(self, plugin: ScannerPlugin) -> None:
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> ScannerPlugin | None:
        return self._plugins.get(name)

    def list_names(self) -> list[str]:
        return sorted(self._plugins.keys())


registry = PluginRegistry()
