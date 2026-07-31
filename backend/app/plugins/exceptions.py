class PluginError(Exception):
    """Raised when a plugin operation fails."""


class PluginNotFoundError(PluginError):
    """Raised when a requested plugin is not registered."""
