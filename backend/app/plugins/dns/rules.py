"""Independent DNS security rules."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.schemas import DnsParsedData

RuleFn = Callable[[DnsParsedData, ScanTarget, str], ScanFinding | None]

_LOW_TTL_SECONDS = 300


def rule_missing_spf(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.has_spf:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MISSING_SPF", asset_id=asset.asset_id,
        title="Missing SPF Record", category="dns",
        evidence="No TXT record containing v=spf1",
        recommendation="Publish an SPF TXT record listing authorized outbound mail servers.",
        reference_links=["https://datatracker.ietf.org/doc/html/rfc7208"],
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_multiple_spf(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.spf_has_duplicate:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MULTIPLE_SPF", asset_id=asset.asset_id,
        title="Multiple SPF Records", category="dns",
        description="More than one SPF TXT record was found, which is invalid per RFC 7208.",
        evidence=f"Found {len(parsed.spf_records)} SPF records",
        recommendation="Merge into a single SPF TXT record at the domain apex.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_spf_too_many_lookups(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.spf_too_many_lookups:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_SPF_TOO_MANY_LOOKUPS", asset_id=asset.asset_id,
        title="SPF Exceeds DNS Lookup Limit", category="dns",
        evidence=f"Estimated {parsed.spf_lookup_count} SPF DNS lookups (limit 10)",
        recommendation="Reduce include/redirect mechanisms to stay within the 10-lookup SPF limit.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_weak_spf(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.spf_record or not parsed.spf_is_weak:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_WEAK_SPF", asset_id=asset.asset_id,
        title="Weak SPF Policy", category="dns", evidence=parsed.spf_record,
        recommendation="Avoid +all, ?all, and ptr mechanisms. End with -all or ~all.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_missing_dmarc(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.dmarc_record:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MISSING_DMARC", asset_id=asset.asset_id,
        title="Missing DMARC Record", category="dns",
        evidence=f"No v=DMARC1 TXT at _dmarc.{parsed.domain}",
        recommendation="Publish a DMARC TXT record at _dmarc.{domain}.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_weak_dmarc(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.dmarc_is_weak:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_WEAK_DMARC", asset_id=asset.asset_id,
        title="Weak DMARC Policy", category="dns",
        evidence=f"DMARC p={parsed.dmarc_policy}",
        recommendation="Upgrade DMARC policy from p=none to quarantine or reject after monitoring.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_dmarc_missing_rua(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.dmarc_record or not parsed.dmarc_missing_rua:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_DMARC_MISSING_RUA", asset_id=asset.asset_id,
        title="DMARC Missing Reporting Address", category="dns",
        evidence="No rua or ruf tag in DMARC record",
        recommendation="Add rua=mailto:... to receive aggregate DMARC reports.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_missing_dkim(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.dkim_selectors_found:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MISSING_DKIM", asset_id=asset.asset_id,
        title="No DKIM Record Found", category="dns",
        evidence="No DKIM TXT at common selectors",
        recommendation="Publish DKIM TXT records for your mail signing selectors.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_dnssec_disabled(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.dnssec_enabled:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_DNSSEC_DISABLED", asset_id=asset.asset_id,
        title="DNSSEC Not Enabled", category="dns",
        evidence=f"No DNSKEY+DS records for {parsed.domain}",
        recommendation="Enable DNSSEC signing with your DNS provider.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_dnssec_incomplete(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.dnssec_incomplete:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_DNSSEC_INCOMPLETE", asset_id=asset.asset_id,
        title="Incomplete DNSSEC Configuration", category="dns",
        evidence="DNSKEY records found but no DS records in parent zone",
        recommendation="Publish DS records at the parent registrar to complete the chain of trust.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_missing_caa(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.caa_present:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MISSING_CAA", asset_id=asset.asset_id,
        title="Missing CAA Records", category="dns",
        evidence=f"No CAA records for {parsed.domain}",
        recommendation="Publish CAA records to restrict which CAs may issue certificates.",
        reference_links=["https://datatracker.ietf.org/doc/html/rfc8659"],
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_missing_mta_sts(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.mta_sts_present or not parsed.mx_records:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MISSING_MTA_STS", asset_id=asset.asset_id,
        title="Missing MTA-STS Policy", category="dns",
        evidence="Domain has MX records but no _mta-sts TXT record",
        recommendation="Publish MTA-STS to enforce TLS for inbound mail.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_missing_tls_rpt(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.tls_rpt_present or not parsed.mx_records:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MISSING_TLS_RPT", asset_id=asset.asset_id,
        title="Missing TLS-RPT Record", category="dns",
        evidence="Domain has MX records but no _smtp._tls TXT record",
        recommendation="Publish TLS-RPT to receive reports on TLS connectivity for mail.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_subdomain_takeover(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.subdomain_takeover_risks:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_SUBDOMAIN_TAKEOVER", asset_id=asset.asset_id,
        title="Potential Subdomain Takeover", category="dns",
        evidence="; ".join(parsed.subdomain_takeover_risks),
        recommendation="Remove dangling CNAME records or reclaim the target service.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_zone_transfer(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.zone_transfer_allowed:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_ZONE_TRANSFER", asset_id=asset.asset_id,
        title="DNS Zone Transfer Allowed", category="dns",
        evidence=f"AXFR succeeded for {parsed.domain}",
        recommendation="Restrict zone transfers to authorized secondary nameservers only.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_mx_misconfigured(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.mx_misconfigured:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_MX_MISCONFIGURED", asset_id=asset.asset_id,
        title="MX Host Does Not Resolve", category="dns",
        evidence=f"MX hosts without A records: {', '.join(parsed.mx_misconfigured)}",
        recommendation="Ensure every MX hostname has a valid A or AAAA record.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_wildcard_detected(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.wildcard_detected:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_WILDCARD_DETECTED", asset_id=asset.asset_id,
        title="Wildcard DNS Detected", category="dns",
        evidence=f"Random subdomain probe resolved for {parsed.domain}",
        recommendation="Remove wildcard records unless required.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


def rule_low_ttl(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.minimum_ttl is None or parsed.minimum_ttl >= _LOW_TTL_SECONDS:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="DNS_LOW_TTL", asset_id=asset.asset_id,
        title="Low DNS TTL", category="dns",
        evidence=f"Minimum TTL: {parsed.minimum_ttl}s",
        recommendation="Review whether very low TTLs are intentional.",
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


RULES: list[RuleFn] = [
    rule_missing_spf,
    rule_multiple_spf,
    rule_spf_too_many_lookups,
    rule_weak_spf,
    rule_missing_dmarc,
    rule_weak_dmarc,
    rule_dmarc_missing_rua,
    rule_missing_dkim,
    rule_dnssec_disabled,
    rule_dnssec_incomplete,
    rule_missing_caa,
    rule_missing_mta_sts,
    rule_missing_tls_rpt,
    rule_subdomain_takeover,
    rule_zone_transfer,
    rule_mx_misconfigured,
    rule_wildcard_detected,
    rule_low_ttl,
]


def evaluate_rules(parsed: DnsParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
