"""Backward-compatible re-exports — prefer app.plugins.base.exceptions."""

from app.plugins.base.exceptions import PluginError, PluginNotFoundError

__all__ = ["PluginError", "PluginNotFoundError"]
