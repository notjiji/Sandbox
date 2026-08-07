"""Recursive SPF DNS lookup counting (RFC 7208)."""

from __future__ import annotations

import re

import dns.resolver

_SPF_V1 = re.compile(r"v=spf1", re.IGNORECASE)
_SPF_LOOKUP_LIMIT = 10
# include:/redirect=/exists: plus standalone a, mx, ptr mechanisms
_SPF_LOOKUP_PATTERN = re.compile(
    r"(?:^|[\s;])(?:include:(?P<include>\S+)|redirect=(?P<redirect>\S+)|exists:(?P<exists>\S+)|(?P<bare>[+]?(?:a|mx|ptr))(?=[\s;:/]|$))",
    re.IGNORECASE,
)


def _find_spf_txt(resolver: dns.resolver.Resolver, domain: str) -> str | None:
    try:
        answer = resolver.resolve(domain.rstrip("."), "TXT")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout):
        return None
    except Exception:
        return None

    for rdata in answer:
        try:
            text = b"".join(rdata.strings).decode("utf-8", errors="replace")
        except AttributeError:
            text = str(rdata).strip('"')
        if _SPF_V1.search(text):
            return text
    return None


def count_spf_dns_lookups(
    domain: str,
    spf_record: str,
    resolver: dns.resolver.Resolver,
    *,
    visited: set[str] | None = None,
    depth: int = 0,
) -> int:
    if depth > _SPF_LOOKUP_LIMIT:
        return _SPF_LOOKUP_LIMIT + 1

    visited = visited or set()
    domain_key = domain.lower().rstrip(".")
    if domain_key in visited:
        return 0
    visited.add(domain_key)

    lookups = 0
    normalized = " ".join(spf_record.split())
    for match in _SPF_LOOKUP_PATTERN.finditer(f" {normalized} "):
        lookups += 1
        if lookups > _SPF_LOOKUP_LIMIT:
            return lookups

        include_domain = match.group("include")
        redirect_domain = match.group("redirect")
        if include_domain:
            nested = _find_spf_txt(resolver, include_domain.rstrip("."))
            if nested:
                lookups += count_spf_dns_lookups(
                    include_domain.rstrip("."), nested, resolver, visited=visited, depth=depth + 1
                )
                if lookups > _SPF_LOOKUP_LIMIT:
                    return lookups
        elif redirect_domain:
            nested = _find_spf_txt(resolver, redirect_domain.rstrip("."))
            if nested:
                return lookups + count_spf_dns_lookups(
                    redirect_domain.rstrip("."), nested, resolver, visited=visited, depth=depth + 1
                )

    return lookups
