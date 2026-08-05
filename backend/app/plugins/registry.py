"""Backward-compatible re-exports — prefer app.plugins.base.registry."""

from app.plugins.base.registry import PluginRegistry, registry

__all__ = ["PluginRegistry", "registry"]
