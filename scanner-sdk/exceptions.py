class ScannerError(Exception):
    """Raised when a scanner plugin fails."""


class PluginNotFoundError(ScannerError):
    """Raised when a requested plugin is not registered."""
