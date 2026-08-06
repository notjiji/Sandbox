"""Standard scanner pipeline — collect → parse → evaluate_rules."""

from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any, Generic, TypeVar

from app.plugins.base.contracts import ScanFinding, ScanOptions, ScanResult
from app.plugins.base.plugin import ScanTarget, ScannerPlugin

TRaw = TypeVar("TRaw")
TParsed = TypeVar("TParsed")


class ScannerPipeline(ScannerPlugin, ABC, Generic[TRaw, TParsed]):
    """Base plugin enforcing the standard internal scan pipeline."""

    @abstractmethod
    async def collect(self, asset: ScanTarget, options: ScanOptions) -> TRaw:
        """Fetch raw data from the target. Must not produce findings."""

    @abstractmethod
    def parse(self, raw: TRaw) -> TParsed:
        """Convert raw responses into structured data."""

    @abstractmethod
    def evaluate_rules(self, parsed: TParsed, asset: ScanTarget) -> list[ScanFinding]:
        """Apply rules to parsed data and return findings."""

    def build_metadata(self, parsed: TParsed) -> dict[str, Any]:
        """Optional metadata derived from parsed data."""
        return {}

    async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
        started_at = datetime.now(UTC)
        raw = await self.collect(asset, options)
        parsed = self.parse(raw)
        findings = self.evaluate_rules(parsed, asset)
        return ScanResult.success(
            plugin=self.id,
            version=self.version,
            started_at=started_at,
            findings=findings,
            metadata=self.build_metadata(parsed),
        )
