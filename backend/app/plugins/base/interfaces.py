from abc import ABC, abstractmethod

from app.plugins.base.plugin import ScannerPlugin


class PluginInterface(ABC):
    """Application-level plugin interface."""

    @abstractmethod
    def get_scanner(self) -> ScannerPlugin:
        """Return the scanner implementation for this plugin."""
