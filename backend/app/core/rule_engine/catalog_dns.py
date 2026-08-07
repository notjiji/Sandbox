"""Declarative DNS rules."""

from app.core.rule_engine.models import RuleSpec
from app.plugins.base.contracts import FindingCheckStatus

DNS_RULES: list[RuleSpec] = [
    RuleSpec(
        finding_code="DNS_MISSING_SPF",
        category="dns",
        condition={"path_falsy": "spf_record"},
        evidence="No TXT record containing v=spf1",
        reference_links=("https://datatracker.ietf.org/doc/html/rfc7208",),
    ),
    RuleSpec(
        finding_code="DNS_MULTIPLE_SPF",
        category="dns",
        condition={"path_truthy": "spf_has_duplicate"},
        evidence="Found {spf_record_count} SPF records",
        description="More than one SPF TXT record was found, which is invalid per RFC 7208.",
    ),
    RuleSpec(
        finding_code="DNS_SPF_TOO_MANY_LOOKUPS",
        category="dns",
        condition={"path_truthy": "spf_too_many_lookups"},
        evidence="Estimated {spf_lookup_count} SPF DNS lookups (limit 10)",
    ),
    RuleSpec(
        finding_code="DNS_WEAK_SPF",
        category="dns",
        condition={"op": "and", "conditions": [{"path_truthy": "spf_record"}, {"path_truthy": "spf_is_weak"}]},
        evidence="{spf_record}",
    ),
    RuleSpec(
        finding_code="DNS_MISSING_DMARC",
        category="dns",
        condition={"path_falsy": "dmarc_record"},
        evidence="No v=DMARC1 TXT at _dmarc.{domain}",
    ),
    RuleSpec(
        finding_code="DNS_WEAK_DMARC",
        category="dns",
        condition={"path_truthy": "dmarc_is_weak"},
        evidence="DMARC p={dmarc_policy}",
    ),
    RuleSpec(
        finding_code="DNS_DMARC_MISSING_RUA",
        category="dns",
        condition={"op": "and", "conditions": [{"path_truthy": "dmarc_record"}, {"path_truthy": "dmarc_missing_rua"}]},
        evidence="No rua or ruf tag in DMARC record",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="DNS_MISSING_DKIM",
        category="dns",
        condition={"path_falsy": "dkim_selectors_found"},
        evidence="No DKIM TXT at common selectors",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="DNS_DNSSEC_DISABLED",
        category="dns",
        condition={"path_falsy": "dnssec_enabled"},
        evidence="No DNSKEY+DS records for {domain}",
    ),
    RuleSpec(
        finding_code="DNS_DNSSEC_INCOMPLETE",
        category="dns",
        condition={"path_truthy": "dnssec_incomplete"},
        evidence="DNSKEY records found but no DS records in parent zone",
    ),
    RuleSpec(
        finding_code="DNS_DNSSEC_INVALID",
        category="dns",
        condition={"path_truthy": "dnssec_validation_failed"},
        evidence="DNSSEC records present but chain failed validation (no AD flag from validating resolver)",
    ),
    RuleSpec(
        finding_code="DNS_MISSING_CAA",
        category="dns",
        condition={"path_falsy": "caa_present"},
        evidence="No CAA records for {domain}",
        status=FindingCheckStatus.WARNING,
        reference_links=("https://datatracker.ietf.org/doc/html/rfc8659",),
    ),
    RuleSpec(
        finding_code="DNS_MISSING_MTA_STS",
        category="dns",
        condition={"op": "and", "conditions": [{"path_nonempty": "mx_records"}, {"path_falsy": "mta_sts_present"}]},
        evidence="Domain has MX records but no _mta-sts TXT record",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="DNS_MISSING_TLS_RPT",
        category="dns",
        condition={"op": "and", "conditions": [{"path_nonempty": "mx_records"}, {"path_falsy": "tls_rpt_present"}]},
        evidence="Domain has MX records but no _smtp._tls TXT record",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="DNS_MISSING_BIMI",
        category="dns",
        condition={"op": "and", "conditions": [{"path_nonempty": "mx_records"}, {"path_falsy": "bimi_present"}]},
        evidence="Domain has MX records but no default._bimi TXT record with v=BIMI1",
        status=FindingCheckStatus.WARNING,
        reference_links=("https://datatracker.ietf.org/doc/html/rfc8616",),
    ),
    RuleSpec(
        finding_code="DNS_SUBDOMAIN_TAKEOVER",
        category="dns",
        condition={"path_nonempty": "subdomain_takeover_risks"},
        evidence="{subdomain_takeover_evidence}",
    ),
    RuleSpec(
        finding_code="DNS_ZONE_TRANSFER",
        category="dns",
        condition={"path_truthy": "zone_transfer_allowed"},
        evidence="AXFR succeeded for {domain}",
    ),
    RuleSpec(
        finding_code="DNS_MX_MISCONFIGURED",
        category="dns",
        condition={"path_nonempty": "mx_misconfigured"},
        evidence="MX hosts without A records: {mx_misconfigured_evidence}",
    ),
    RuleSpec(
        finding_code="DNS_WILDCARD_DETECTED",
        category="dns",
        condition={"path_truthy": "wildcard_detected"},
        evidence="Random subdomain probe resolved for {domain}",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="DNS_LOW_TTL",
        category="dns",
        condition={
            "op": "and",
            "conditions": [
                {"op": "truthy", "path": "minimum_ttl"},
                {"op": "lt", "path": "minimum_ttl", "value": 300},
            ],
        },
        evidence="Minimum TTL: {minimum_ttl}s",
        status=FindingCheckStatus.WARNING,
    ),
    RuleSpec(
        finding_code="DNS_RESOLVER_DISCREPANCY",
        category="dns",
        condition={"path_nonempty": "resolver_discrepancies"},
        evidence="{resolver_discrepancy_evidence}",
        status=FindingCheckStatus.WARNING,
    ),
]
