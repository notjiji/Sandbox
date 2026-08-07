"""Independent WHOIS security rules."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.schemas import WhoisParsedData

RuleFn = Callable[[WhoisParsedData, ScanTarget, str], ScanFinding | None]


def rule_expired(parsed: WhoisParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.is_expired:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="WHOIS_EXPIRED",
        asset_id=asset.asset_id,
        title="Domain Registration Expired",
        category="domain",
        evidence=f"WHOIS expiration date: {parsed.expires.isoformat() if parsed.expires else 'unknown'}",
        recommendation="Renew the domain registration immediately to avoid service disruption or loss of the domain.",
        severity=FindingSeverity.CRITICAL,
        status=FindingCheckStatus.FAILED,
    )


def rule_expiring_soon(parsed: WhoisParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.is_expired or not parsed.expiring_soon or parsed.days_until_expiry is None:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="WHOIS_EXPIRING_SOON",
        asset_id=asset.asset_id,
        title="Domain Expiring Soon",
        category="domain",
        evidence=f"Registration expires in {parsed.days_until_expiry} days",
        recommendation="Renew the domain registration before expiry.",
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


def rule_privacy_disabled(parsed: WhoisParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.privacy_disabled:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="WHOIS_PRIVACY_DISABLED",
        asset_id=asset.asset_id,
        title="WHOIS Privacy Disabled",
        category="domain",
        evidence="Registrant contact details appear publicly visible in WHOIS",
        recommendation="Enable registrar WHOIS privacy/redaction to reduce exposure of contact information.",
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


def rule_unknown_registrar(parsed: WhoisParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.unknown_registrar:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="WHOIS_UNKNOWN_REGISTRAR",
        asset_id=asset.asset_id,
        title="Unknown Domain Registrar",
        category="domain",
        evidence=f"Registrar field missing or unknown for {parsed.domain}",
        recommendation="Verify domain registration records and ensure the domain is managed through a trusted registrar.",
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.WARNING,
    )


RULES: list[RuleFn] = [
    rule_expired,
    rule_expiring_soon,
    rule_privacy_disabled,
    rule_unknown_registrar,
]


def evaluate_rules(parsed: WhoisParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
