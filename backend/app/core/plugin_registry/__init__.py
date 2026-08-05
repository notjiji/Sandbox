"""Platform-level plugin registry (infrastructure layer)."""

from app.plugins.base.registry import PluginRegistry, registry

__all__ = ["PluginRegistry", "registry"]
