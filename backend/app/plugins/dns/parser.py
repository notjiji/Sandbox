"""Convert raw DNS data into structured analysis."""

from app.plugins.dns.schemas import DnsParsedData, DnsRawResponse
from app.plugins.dns.utils import (
    dkim_selector_names,
    estimate_spf_lookup_count,
    find_dmarc_record,
    find_spf_record,
    is_dangling_cname_target,
    is_weak_spf,
    parse_dmarc_policy,
)

_SPF_LOOKUP_LIMIT = 10


def _minimum_ttl(raw: DnsRawResponse) -> int | None:
    ttl_values = [ttl for ttl in raw.ttls.values() if ttl is not None]
    return min(ttl_values) if ttl_values else None


def _subdomain_takeover_risks(raw: DnsRawResponse) -> list[str]:
    risks: list[str] = []
    for probe in raw.subdomain_probes:
        if probe.cname_target and is_dangling_cname_target(probe.cname_target):
            risks.append(f"{probe.subdomain} CNAME {probe.cname_target}")
    return risks


def _mx_misconfigured(raw: DnsRawResponse) -> list[str]:
    return [probe.host for probe in raw.mx_probes if not probe.a_records]


def parse(raw: DnsRawResponse) -> DnsParsedData:
    txt_records = raw.records.get("TXT", [])
    spf_records = raw.spf_records or []
    spf_record = find_spf_record(txt_records)
    spf_lookup_count = estimate_spf_lookup_count(spf_record) if spf_record else 0
    dmarc_record = find_dmarc_record(raw.dmarc_records)
    dmarc_policy, dmarc_is_weak, dmarc_missing_rua = (
        parse_dmarc_policy(dmarc_record) if dmarc_record else (None, False, False)
    )

    has_dnskey = bool(raw.dnskey_records)
    has_ds = bool(raw.ds_records)
    has_rrsig = bool(raw.rrsig_records)

    return DnsParsedData(
        domain=raw.domain,
        a_records=raw.records.get("A", []),
        aaaa_records=raw.records.get("AAAA", []),
        mx_records=raw.records.get("MX", []),
        txt_records=txt_records,
        ns_records=raw.records.get("NS", []),
        soa_record=(raw.records.get("SOA") or [None])[0],
        cname_records=raw.records.get("CNAME", []),
        spf_record=spf_record,
        spf_records=spf_records,
        spf_is_weak=is_weak_spf(spf_record) if spf_record else False,
        spf_has_duplicate=len(spf_records) > 1,
        spf_lookup_count=spf_lookup_count,
        spf_too_many_lookups=spf_lookup_count > _SPF_LOOKUP_LIMIT,
        dmarc_record=dmarc_record,
        dmarc_policy=dmarc_policy,
        dmarc_is_weak=dmarc_is_weak,
        dmarc_missing_rua=dmarc_missing_rua,
        dkim_selectors_found=dkim_selector_names(raw.dkim_records),
        dnssec_enabled=has_dnskey and has_ds,
        dnssec_has_ds=has_ds,
        dnssec_has_rrsig=has_rrsig,
        dnssec_incomplete=has_dnskey and not has_ds,
        caa_records=raw.caa_records,
        caa_present=bool(raw.caa_records),
        mta_sts_present=any("v=STSv1" in record for record in raw.mta_sts_records),
        tls_rpt_present=any("v=TLSRPTv1" in record for record in raw.tls_rpt_records),
        bimi_present=any("v=BIMI1" in record for record in raw.bimi_records),
        wildcard_detected=raw.wildcard_resolves,
        minimum_ttl=_minimum_ttl(raw),
        subdomain_takeover_risks=_subdomain_takeover_risks(raw),
        mx_misconfigured=_mx_misconfigured(raw),
        zone_transfer_allowed=raw.zone_transfer_allowed,
    )
