"""Certificate Transparency issuer analysis via crt.sh."""

from __future__ import annotations

import re

from app.plugins.dns.crtsh import fetch_crtsh_entries

_TRUSTED_CA_MARKERS = (
    "let's encrypt",
    "lets encrypt",
    "digicert",
    "google trust",
    "amazon",
    "amazon rsa",
    "cloudflare",
    "sectigo",
    "comodo",
    "globalsign",
    "godaddy",
    "microsoft",
    "identrust",
    "zerossl",
    "buypass",
    "ssl.com",
    "swisssign",
    "harica",
    "quovadis",
)


def _normalize_issuer(issuer: str) -> str:
    return re.sub(r"\s+", " ", issuer.lower()).strip()


def _issuer_organization(issuer: str) -> str:
    match = re.search(r"\bO=([^,]+)", issuer, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower()
    return _normalize_issuer(issuer)


def is_trusted_ca_issuer(issuer: str) -> bool:
    normalized = _normalize_issuer(issuer)
    return any(marker in normalized for marker in _TRUSTED_CA_MARKERS)


def issuers_match(left: str, right: str) -> bool:
    left_org = _issuer_organization(left)
    right_org = _issuer_organization(right)
    if left_org == right_org:
        return True
    return left_org in right_org or right_org in left_org


def analyze_ct_issuers(domain: str, live_issuer: str | None) -> tuple[list[str], list[str]]:
    entries = fetch_crtsh_entries(domain)
    issuers = sorted({_normalize_issuer(entry.get("issuer_name", "")) for entry in entries if entry.get("issuer_name")})
    if not issuers:
        return [], []

    suspicious: list[str] = []
    live = live_issuer or ""
    for issuer in issuers:
        if is_trusted_ca_issuer(issuer):
            if live and not issuers_match(live, issuer):
                suspicious.append(issuer)
            continue
        suspicious.append(issuer)
    return issuers, list(dict.fromkeys(suspicious))
