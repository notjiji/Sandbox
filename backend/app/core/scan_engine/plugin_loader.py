"""Backward-compatible re-exports — prefer app.plugins.base.loader."""

from app.plugins.base.loader import PluginLoader, PluginSelection, plugin_loader

__all__ = ["PluginLoader", "PluginSelection", "plugin_loader"]
