from app.plugins.exceptions import PluginNotFoundError
from app.plugins.registry import registry


class PluginManager:
    """Resolve and invoke registered scanner plugins."""

    def get_plugin(self, name: str):
        plugin = registry.get(name)
        if plugin is None:
            raise PluginNotFoundError(f"Plugin not found: {name}")
        return plugin

    def list_plugins(self) -> list[str]:
        return registry.list_names()


manager = PluginManager()
