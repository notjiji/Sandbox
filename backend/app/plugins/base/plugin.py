from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.plugins.base.config import PluginConfig
from app.plugins.base.output import PluginOutput
from app.scans.enums import ScanType


@dataclass(frozen=True)
class ScanTarget:
    """Normalized asset passed to scanner plugins (plugin-facing contract)."""

    asset_id: str
    identifier: str
    asset_type: str


class ScannerPlugin(ABC):
    """Base interface every scanner plugin must implement."""

    name: str
    description: str
    supported_assets: list[str]
    supported_scan_types: list[str]
    default_config: PluginConfig

    @property
    def config(self) -> PluginConfig:
        return self.default_config

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def version(self) -> str:
        return self.config.version

    def supports_asset(self, asset_type: str) -> bool:
        if not self.supported_assets:
            return True
        return asset_type in self.supported_assets

    def supports_scan_type(self, scan_type: ScanType) -> bool:
        return scan_type.value in self.supported_scan_types

    @abstractmethod
    async def scan(self, asset: ScanTarget) -> PluginOutput:
        """Execute a scan and return the standard plugin output structure."""
