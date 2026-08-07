"""Certificate Transparency subdomain discovery via crt.sh."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

_DKIM_PATTERN = re.compile(r"^([^.]+)\._domainkey\.(.+)$", re.IGNORECASE)
_CRTSH_TIMEOUT = 15


def fetch_crtsh_entries(domain: str) -> list[dict]:
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    request = urllib.request.Request(url, headers={"User-Agent": "Sandbox-DNS-Scanner/3.1"})
    try:
        with urllib.request.urlopen(request, timeout=_CRTSH_TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, ValueError):
        return []

    if not isinstance(payload, list):
        return []
    return payload


def fetch_crtsh_names(domain: str) -> list[str]:
    payload = fetch_crtsh_entries(domain)
    names: set[str] = set()
    for entry in payload:
        name_value = entry.get("name_value", "")
        for line in name_value.splitlines():
            cleaned = line.strip().lower().rstrip(".")
            if cleaned.endswith(f".{domain}") or cleaned == domain:
                names.add(cleaned)
    return sorted(names)


def extract_dkim_selectors(names: list[str], domain: str) -> list[str]:
    selectors: set[str] = set()
    for name in names:
        match = _DKIM_PATTERN.match(name)
        if match and match.group(2) == domain:
            selectors.add(match.group(1))
    return sorted(selectors)


def subdomains_from_ct(names: list[str], domain: str, *, limit: int = 100) -> list[str]:
    subs: list[str] = []
    for name in names:
        if name == domain:
            continue
        if name.endswith(f".{domain}"):
            subs.append(name[: -(len(domain) + 1)])
    return subs[:limit]
