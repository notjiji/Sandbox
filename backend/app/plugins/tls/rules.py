from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.tls.schemas import TlsParsedData


def evaluate_rules(parsed: TlsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    if not parsed.weak_cipher:
        return []

    return [
        scan_finding(
            plugin=plugin_id,
            rule_id="TLS_WEAK_CIPHER",
            asset_id=asset.asset_id,
            title="Weak Cipher Suite Negotiated",
            category="transport",
            evidence=f"{parsed.negotiated_cipher} accepted",
            recommendation="Disable weak cipher suites and prefer AEAD ciphers.",
            severity=FindingSeverity.HIGH,
            status=FindingCheckStatus.FAILED,
        )
    ]
