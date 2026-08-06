from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.plugins.base.config import PluginConfig
from app.plugins.base.contracts import ScanOptions, ScanResult
from app.scans.enums import ScanType


@dataclass(frozen=True)
class ScanTarget:
    """Normalized asset passed to scanner plugins (plugin-facing contract)."""

    asset_id: str
    identifier: str
    asset_type: str


class ScannerPlugin(ABC):
    """Base interface every scanner plugin must implement."""

    id: str
    name: str
    version: str
    supported_asset_types: list[str]
    supported_scan_types: list[str]
    default_config: PluginConfig

    @property
    def config(self) -> PluginConfig:
        return self.default_config

    @property
    def enabled(self) -> bool:
        return self.config.enabled

    @property
    def description(self) -> str:
        """Display label — alias of name for registry consumers."""
        return self.name

    @property
    def supported_assets(self) -> list[str]:
        """Backward-compatible alias."""
        return self.supported_asset_types

    def default_options(self) -> ScanOptions:
        return ScanOptions(
            timeout=self.config.timeout,
            retries=self.config.retries,
            parallel=self.config.parallel,
        )

    def supports_asset(self, asset_type: str) -> bool:
        if not self.supported_asset_types:
            return True
        return asset_type in self.supported_asset_types

    def supports_scan_type(self, scan_type: ScanType) -> bool:
        return scan_type.value in self.supported_scan_types

    @abstractmethod
    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        """Execute a scan and return the standard ScanResult structure."""
