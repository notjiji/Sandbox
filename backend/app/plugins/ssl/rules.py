"""Evaluate SSL/TLS rules against parsed data."""

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.schemas import SslParsedData


def evaluate_rules(parsed: SslParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []

    if any(version in ("TLSv1.0", "TLS1.0") for version in parsed.protocols):
        findings.append(
            scan_finding(
                plugin=plugin_id,
                rule_id="SSL_TLS10_ENABLED",
                asset_id=asset.asset_id,
                title="TLS 1.0 Enabled",
                description="The endpoint accepts deprecated TLS 1.0 connections.",
                category="transport",
                evidence="TLS 1.0 cipher suite accepted",
                recommendation="Disable TLS 1.0 and enforce TLS 1.2 or higher.",
                reference_links=["https://datatracker.ietf.org/doc/rfc8996/"],
                severity=FindingSeverity.HIGH,
                status=FindingCheckStatus.FAILED,
            )
        )

    return findings
