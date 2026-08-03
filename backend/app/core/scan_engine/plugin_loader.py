"""Loads scanner plugins from app.plugins.* into the plugin registry."""

from dataclasses import dataclass

from app.core.plugin_registry import registry
from app.plugins.exceptions import PluginNotFoundError
from app.plugins.manager import manager


@dataclass(frozen=True)
class EnabledPluginSet:
    enabled: list[str]
    skipped: list[str]


class PluginLoader:
    def load_all(self) -> list[str]:
        """Discover and register built-in plugins. Returns registered names."""
        from app.plugins import discover_plugins

        return discover_plugins(registry)

    def load_enabled(self, plugin_names: list[str]) -> EnabledPluginSet:
        """Register plugins and return enabled vs skipped names for this scan."""
        self.load_all()

        enabled: list[str] = []
        skipped: list[str] = []
        for name in plugin_names:
            try:
                plugin = manager.get_plugin(name)
            except PluginNotFoundError:
                skipped.append(name)
                continue
            if getattr(plugin, "enabled", True):
                enabled.append(name)
            else:
                skipped.append(name)
        return EnabledPluginSet(enabled=enabled, skipped=skipped)
