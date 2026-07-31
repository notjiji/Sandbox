"""Loads scanner plugins from app.plugins.* into the plugin registry."""

from app.core.plugin_registry import registry


class PluginLoader:
    def load_all(self) -> list[str]:
        """Discover and register built-in plugins. Returns registered names."""
        from app.plugins import discover_plugins

        return discover_plugins(registry)
