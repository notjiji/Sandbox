"""security.txt validation rules per RFC 9116."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.security_txt.schemas import SecurityTxtParsedData

RuleFn = Callable[[SecurityTxtParsedData, ScanTarget, str], ScanFinding | None]


def rule_missing(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.present:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_MISSING",
        asset_id=asset.asset_id,
        title="Missing security.txt",
        category="exposure",
        evidence="/.well-known/security.txt was not found or returned an empty response",
        recommendation="Publish a security.txt file with Contact and disclosure details per RFC 9116.",
        reference_links=["https://securitytxt.org/"],
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


def rule_missing_contact(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or parsed.has_required_contact:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_MISSING_CONTACT",
        asset_id=asset.asset_id,
        title="security.txt Missing Contact",
        category="exposure",
        evidence="security.txt is present but does not define a Contact field",
        recommendation="Add at least one Contact field with a mailto: or https: URI.",
        reference_links=["https://datatracker.ietf.org/doc/html/rfc9116"],
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.FAILED,
    )


def rule_invalid_contact(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or parsed.contact_valid or not parsed.has_required_contact:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_INVALID_CONTACT",
        asset_id=asset.asset_id,
        title="security.txt Invalid Contact",
        category="exposure",
        evidence=f"Invalid Contact value(s): {', '.join(parsed.contacts[:3])}",
        recommendation="Use mailto: or https: URIs for Contact fields.",
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.FAILED,
    )


def rule_expired(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or not parsed.expires_expired:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_EXPIRED",
        asset_id=asset.asset_id,
        title="security.txt Expired",
        category="exposure",
        evidence=f"Expires field is in the past: {parsed.expires}",
        recommendation="Update the Expires field to a future ISO 8601 timestamp.",
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.FAILED,
    )


def rule_missing_expires(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or parsed.expires:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_MISSING_EXPIRES",
        asset_id=asset.asset_id,
        title="security.txt Missing Expires",
        category="exposure",
        evidence="security.txt does not define an Expires field",
        recommendation="Add an Expires field so researchers know when to re-check the file.",
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


def rule_invalid_encryption(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or parsed.encryption_valid or not parsed.encryption:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_INVALID_ENCRYPTION",
        asset_id=asset.asset_id,
        title="security.txt Invalid Encryption",
        category="exposure",
        evidence=f"Invalid Encryption URI(s): {', '.join(parsed.encryption[:3])}",
        recommendation="Point Encryption to a valid HTTPS URI hosting your OpenPGP key.",
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


def rule_invalid_canonical(parsed: SecurityTxtParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.present or not parsed.canonical:
        return None
    if parsed.canonical_valid and parsed.canonical_matches is not False:
        return None
    evidence = "Canonical URI is invalid or does not match the downloaded security.txt location"
    if parsed.canonical:
        evidence = f"{evidence}: {parsed.canonical[0]}"
    return scan_finding(
        plugin=plugin_id,
        rule_id="SECURITY_TXT_INVALID_CANONICAL",
        asset_id=asset.asset_id,
        title="security.txt Invalid Canonical",
        category="exposure",
        evidence=evidence,
        recommendation="Set Canonical to the authoritative HTTPS URL of your security.txt file.",
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


RULES: list[RuleFn] = [
    rule_missing,
    rule_missing_contact,
    rule_invalid_contact,
    rule_expired,
    rule_missing_expires,
    rule_invalid_encryption,
    rule_invalid_canonical,
]


def evaluate_rules(parsed: SecurityTxtParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
