from abc import ABC, abstractmethod

from scanner_sdk.contracts import ScanResult, ScanTarget


class ScannerPlugin(ABC):
    """Base class for all scanner plugins."""

    name: str
    version: str

    @abstractmethod
    def scan(self, target: ScanTarget) -> ScanResult:
        """Execute a scan against the given target."""
