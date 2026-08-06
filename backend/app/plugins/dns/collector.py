"""Collect raw DNS records via dnspython — no findings."""

from __future__ import annotations

import asyncio

import dns.exception
import dns.query
import dns.rdatatype
import dns.resolver
import dns.zone

from app.plugins.base.contracts import ScanOptions
from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.schemas import DnsRawResponse, MxHostProbe, SubdomainCnameProbe
from app.plugins.dns.utils import (
    _COMMON_DKIM_SELECTORS,
    _COMMON_SUBDOMAINS,
    extract_domain,
    find_spf_records,
    parse_mx_host,
    wildcard_probe_name,
)

_RECORD_TYPES = ("A", "AAAA", "MX", "TXT", "NS", "SOA", "CNAME")
_EXTRA_TYPES = ("DNSKEY", "DS", "RRSIG", "CAA")


def _format_rdata(rdata) -> str:
    if rdata.rdtype == dns.rdatatype.MX:
        return f"{rdata.preference} {str(rdata.exchange).rstrip('.')}"
    if rdata.rdtype == dns.rdatatype.SOA:
        return str(rdata)
    if rdata.rdtype == dns.rdatatype.TXT:
        try:
            return b"".join(rdata.strings).decode("utf-8", errors="replace")
        except AttributeError:
            return str(rdata).strip('"')
    return str(rdata).rstrip(".")


def _make_resolver(timeout: float) -> dns.resolver.Resolver:
    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout
    return resolver


def _query(
    resolver: dns.resolver.Resolver, domain: str, rdtype: str
) -> tuple[list[str], int | None, str | None]:
    try:
        answer = resolver.resolve(domain, rdtype)
        values = [_format_rdata(rdata) for rdata in answer]
        ttl = answer.rrset.ttl if answer.rrset is not None else None
        return values, ttl, None
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout) as exc:
        return [], None, str(exc)
    except Exception as exc:
        return [], None, str(exc)


def _query_dkim(resolver: dns.resolver.Resolver, domain: str) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for selector in _COMMON_DKIM_SELECTORS:
        name = f"{selector}._domainkey.{domain}"
        values, _, _ = _query(resolver, name, "TXT")
        if values:
            found[selector] = values
    return found


def _probe_subdomains(resolver: dns.resolver.Resolver, domain: str) -> list[SubdomainCnameProbe]:
    probes: list[SubdomainCnameProbe] = []
    for label in _COMMON_SUBDOMAINS:
        fqdn = f"{label}.{domain}"
        cnames, _, _ = _query(resolver, fqdn, "CNAME")
        a_records, _, _ = _query(resolver, fqdn, "A")
        probes.append(
            SubdomainCnameProbe(
                subdomain=fqdn,
                cname_target=cnames[0] if cnames else None,
                resolves=bool(cnames or a_records),
            )
        )
    return probes


def _probe_mx_hosts(resolver: dns.resolver.Resolver, mx_records: list[str]) -> list[MxHostProbe]:
    probes: list[MxHostProbe] = []
    seen: set[str] = set()
    for mx in mx_records:
        host = parse_mx_host(mx)
        if host in seen:
            continue
        seen.add(host)
        a_records, _, _ = _query(resolver, host, "A")
        ptr_records: list[str] = []
        for ip in a_records:
            ptr_values, _, _ = _query(resolver, ip, "PTR")
            ptr_records.extend(ptr_values)
        probes.append(MxHostProbe(host=host, a_records=a_records, ptr_records=ptr_records))
    return probes


def _attempt_zone_transfer(resolver: dns.resolver.Resolver, domain: str, ns_records: list[str]) -> bool:
    for ns in ns_records[:2]:
        try:
            ns_host = ns.rstrip(".")
            dns.zone.from_xfr(dns.query.xfr(ns_host, domain, lifetime=resolver.lifetime))
            return True
        except Exception:
            continue
    return False


def _collect_sync(domain: str, timeout: float) -> DnsRawResponse:
    resolver = _make_resolver(timeout)
    records: dict[str, list[str]] = {}
    ttls: dict[str, int | None] = {}
    query_errors: dict[str, str] = {}

    for rdtype in _RECORD_TYPES:
        values, ttl, error = _query(resolver, domain, rdtype)
        records[rdtype] = values
        ttls[rdtype] = ttl
        if error:
            query_errors[rdtype] = error

    extra: dict[str, list[str]] = {}
    for rdtype in _EXTRA_TYPES:
        values, _, error = _query(resolver, domain, rdtype)
        extra[rdtype] = values
        if error:
            query_errors[rdtype] = error

    dmarc_records, _, dmarc_error = _query(resolver, f"_dmarc.{domain}", "TXT")
    if dmarc_error:
        query_errors["DMARC"] = dmarc_error

    mta_sts_records, _, _ = _query(resolver, f"_mta-sts.{domain}", "TXT")
    tls_rpt_records, _, _ = _query(resolver, f"_smtp._tls.{domain}", "TXT")
    bimi_records, _, _ = _query(resolver, f"default._bimi.{domain}", "TXT")

    dkim_records = _query_dkim(resolver, domain)
    subdomain_probes = _probe_subdomains(resolver, domain)
    mx_probes = _probe_mx_hosts(resolver, records.get("MX", []))

    probe_name = wildcard_probe_name(domain)
    wildcard_values, _, _ = _query(resolver, probe_name, "A")
    if not wildcard_values:
        wildcard_values, _, _ = _query(resolver, probe_name, "AAAA")

    zone_transfer_allowed = _attempt_zone_transfer(resolver, domain, records.get("NS", []))

    return DnsRawResponse(
        domain=domain,
        records=records,
        ttls=ttls,
        spf_records=find_spf_records(records.get("TXT", [])),
        dnskey_records=extra.get("DNSKEY", []),
        ds_records=extra.get("DS", []),
        rrsig_records=extra.get("RRSIG", []),
        caa_records=extra.get("CAA", []),
        dkim_records=dkim_records,
        dmarc_records=dmarc_records,
        mta_sts_records=mta_sts_records,
        tls_rpt_records=tls_rpt_records,
        bimi_records=bimi_records,
        subdomain_probes=subdomain_probes,
        mx_probes=mx_probes,
        wildcard_probe=probe_name,
        wildcard_resolves=bool(wildcard_values),
        zone_transfer_allowed=zone_transfer_allowed,
        query_errors=query_errors,
    )


async def collect(asset: ScanTarget, options: ScanOptions) -> DnsRawResponse:
    domain = extract_domain(asset.identifier)
    return await asyncio.to_thread(_collect_sync, domain, options.timeout)
