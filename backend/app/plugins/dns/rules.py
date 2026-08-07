"""DNS rules — evaluated by the declarative rule engine."""

from collections.abc import Callable

from app.core.rule_engine.catalog import get_plugin_rules
from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.schemas import DnsParsedData

RuleFn = Callable[[DnsParsedData, ScanTarget, str], object | None]


def _single_rule(finding_code: str) -> RuleFn:
    rules = [rule for rule in get_plugin_rules("dns") if rule.finding_code == finding_code]

    def evaluate(parsed: DnsParsedData, asset: ScanTarget, plugin_id: str):
        findings = evaluate_plugin_rules("dns", parsed, asset, rules=rules)
        return findings[0] if findings else None

    return evaluate


rule_missing_spf = _single_rule("DNS_MISSING_SPF")
rule_multiple_spf = _single_rule("DNS_MULTIPLE_SPF")
rule_spf_too_many_lookups = _single_rule("DNS_SPF_TOO_MANY_LOOKUPS")
rule_weak_spf = _single_rule("DNS_WEAK_SPF")
rule_missing_dmarc = _single_rule("DNS_MISSING_DMARC")
rule_weak_dmarc = _single_rule("DNS_WEAK_DMARC")
rule_dmarc_missing_rua = _single_rule("DNS_DMARC_MISSING_RUA")
rule_missing_dkim = _single_rule("DNS_MISSING_DKIM")
rule_dnssec_disabled = _single_rule("DNS_DNSSEC_DISABLED")
rule_dnssec_incomplete = _single_rule("DNS_DNSSEC_INCOMPLETE")
rule_dnssec_invalid = _single_rule("DNS_DNSSEC_INVALID")
rule_missing_caa = _single_rule("DNS_MISSING_CAA")
rule_missing_mta_sts = _single_rule("DNS_MISSING_MTA_STS")
rule_missing_tls_rpt = _single_rule("DNS_MISSING_TLS_RPT")
rule_subdomain_takeover = _single_rule("DNS_SUBDOMAIN_TAKEOVER")
rule_zone_transfer = _single_rule("DNS_ZONE_TRANSFER")
rule_mx_misconfigured = _single_rule("DNS_MX_MISCONFIGURED")
rule_wildcard_detected = _single_rule("DNS_WILDCARD_DETECTED")
rule_low_ttl = _single_rule("DNS_LOW_TTL")
rule_resolver_discrepancy = _single_rule("DNS_RESOLVER_DISCREPANCY")


def evaluate_rules(parsed: DnsParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules("dns", parsed, asset)
