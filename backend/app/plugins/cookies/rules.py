from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies.schemas import CookiesParsedData


def evaluate_rules(parsed: CookiesParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []

    for cookie in parsed.session_cookies:
        if not cookie.secure:
            findings.append(
                scan_finding(
                    plugin=plugin_id,
                    rule_id="COOKIE_MISSING_SECURE",
                    asset_id=asset.asset_id,
                    title="Session Cookie Missing Secure Flag",
                    category="cookies",
                    evidence=f"Set-Cookie: {cookie.name} without Secure",
                    recommendation="Set the Secure attribute on session cookies.",
                    severity=FindingSeverity.HIGH,
                    status=FindingCheckStatus.FAILED,
                )
            )
        if not cookie.httponly:
            findings.append(
                scan_finding(
                    plugin=plugin_id,
                    rule_id="COOKIE_MISSING_HTTPONLY",
                    asset_id=asset.asset_id,
                    title="Session Cookie Missing HttpOnly Flag",
                    category="cookies",
                    evidence=f"Set-Cookie: {cookie.name} without HttpOnly",
                    recommendation="Set the HttpOnly attribute on session cookies.",
                    severity=FindingSeverity.MEDIUM,
                    status=FindingCheckStatus.FAILED,
                )
            )

    return findings
