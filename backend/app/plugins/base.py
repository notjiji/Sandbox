from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.scans.enums import ScanType


@dataclass(frozen=True)
class ScanTarget:
    """Normalized asset passed to scanner plugins (plugin-facing contract)."""

    asset_id: str
    identifier: str
    asset_type: str


@dataclass
class ScanResult:
    success: bool
    findings: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ScannerPlugin(ABC):
    """Base interface every scanner plugin must implement."""

    name: str
    description: str
    version: str
    supported_assets: list[str]
    supported_scan_types: list[str]
    enabled: bool = True

    def supports_asset(self, asset_type: str) -> bool:
        if not self.supported_assets:
            return True
        return asset_type in self.supported_assets

    def supports_scan_type(self, scan_type: ScanType) -> bool:
        return scan_type.value in self.supported_scan_types

    @abstractmethod
    async def scan(self, asset: ScanTarget) -> ScanResult:
        """Execute a scan against the normalized asset target."""
