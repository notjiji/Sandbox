from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.schemas import HttpHeadersParsedData


def evaluate_rules(parsed: HttpHeadersParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []

    if not parsed.has_csp:
        findings.append(
            scan_finding(
                plugin=plugin_id,
                rule_id="HTTP_NO_CSP",
                asset_id=asset.asset_id,
                title="Missing Content Security Policy",
                category="headers",
                evidence="Header not present",
                recommendation="Add a Content-Security-Policy header.",
                severity=FindingSeverity.MEDIUM,
                status=FindingCheckStatus.FAILED,
            )
        )

    if not parsed.has_hsts:
        findings.append(
            scan_finding(
                plugin=plugin_id,
                rule_id="HTTP_NO_HSTS",
                asset_id=asset.asset_id,
                title="Missing Strict Transport Security",
                category="headers",
                evidence="HSTS header not present",
                recommendation="Add Strict-Transport-Security with a long max-age.",
                severity=FindingSeverity.HIGH,
                status=FindingCheckStatus.FAILED,
            )
        )

    return findings
