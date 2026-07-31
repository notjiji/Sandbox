from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScanTarget:
    asset_id: str
    identifier: str
    asset_type: str


@dataclass
class ScanResult:
    success: bool
    findings: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


class ScannerPlugin(ABC):
    """Base class for in-process scanner plugins."""

    name: str
    version: str

    @abstractmethod
    def scan(self, target: ScanTarget) -> ScanResult:
        """Execute a scan against the given target."""
