"""Fingerprinting is metadata-only — no security findings."""

from app.plugins.base.contracts import ScanFinding
from app.plugins.base.plugin import ScanTarget
from app.plugins.fingerprint.schemas import FingerprintParsedData


def evaluate_rules(
    parsed: FingerprintParsedData,
    asset: ScanTarget,
    *,
    plugin_id: str,
) -> list[ScanFinding]:
    return []
