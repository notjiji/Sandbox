"""Software version detection and OSV vulnerability lookup."""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from dataclasses import dataclass

_OSV_URL = "https://api.osv.dev/v1/query"
_OSV_TIMEOUT = 20
_PRODUCT_PATTERNS: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (re.compile(r"nginx/([\d.]+)", re.I), "nginx", "Debian"),
    (re.compile(r"Apache/([\d.]+)", re.I), "apache2", "Debian"),
    (re.compile(r"PHP/([\d.]+)", re.I), "php", "Packagist"),
    (re.compile(r"OpenSSL/([\d.]+)", re.I), "openssl", "Debian"),
    (re.compile(r"Microsoft-IIS/([\d.]+)", re.I), "iis", "Debian"),
    (re.compile(r"Express(?:/([\d.]+))?", re.I), "express", "npm"),
)
_SSH_PATTERN = re.compile(r"OpenSSH[_\s-]?([\d.p]+)", re.I)
_SERVICE_ECOSYSTEMS: dict[str, str] = {
    "nginx": "Debian",
    "apache": "Debian",
    "apache httpd": "Debian",
    "openssh": "Debian",
    "mysql": "Debian",
    "mariadb": "Debian",
    "redis": "Debian",
    "mongodb": "Debian",
    "postgresql": "Debian",
    "php": "Packagist",
    "iis": "Debian",
    "express": "npm",
}
_PRODUCT_ALIASES: dict[str, str] = {
    "apache httpd": "apache2",
    "apache": "apache2",
    "openssh": "openssh",
    "mariadb": "mysql",
}


@dataclass(frozen=True)
class SoftwareHint:
    product: str
    version: str
    ecosystem: str
    source: str


def hints_from_http_headers(headers: dict[str, str]) -> list[SoftwareHint]:
    hints: list[SoftwareHint] = []
    for header_name in ("server", "x-powered-by", "x-aspnet-version"):
        value = next((v for k, v in headers.items() if k.lower() == header_name), None)
        if not value:
            continue
        for pattern, product, ecosystem in _PRODUCT_PATTERNS:
            match = pattern.search(value)
            if not match:
                continue
            version = match.group(1) if match.lastindex else "0"
            hints.append(SoftwareHint(product=product, version=version, ecosystem=ecosystem, source=header_name))
    return hints


def hints_from_ssh_banner(banner: str | None) -> list[SoftwareHint]:
    if not banner:
        return []
    match = _SSH_PATTERN.search(banner)
    if not match:
        return []
    return [SoftwareHint(product="openssh", version=match.group(1), ecosystem="Debian", source="ssh-banner")]


def hints_from_services(services: list[dict]) -> list[SoftwareHint]:
    hints: list[SoftwareHint] = []
    for service in services:
        product = (service.get("product") or service.get("service") or "").strip()
        version = (service.get("version") or "").strip()
        if not product or not version:
            banner = service.get("banner")
            if isinstance(banner, str):
                hints.extend(hints_from_ssh_banner(banner))
            continue
        normalized = product.lower()
        osv_product = _PRODUCT_ALIASES.get(normalized, normalized.replace(" ", ""))
        ecosystem = _SERVICE_ECOSYSTEMS.get(normalized, "Debian")
        port = service.get("port")
        source = f"port-{port}" if port is not None else "port-scan"
        hints.append(SoftwareHint(product=osv_product, version=version, ecosystem=ecosystem, source=source))
    return hints


def query_osv(product: str, version: str, ecosystem: str) -> list[dict]:
    payload = {
        "package": {"name": product, "ecosystem": ecosystem},
        "version": version,
    }
    request = urllib.request.Request(
        _OSV_URL,
        data=__import__("json").dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": "Sandbox-CVE-Scanner/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_OSV_TIMEOUT) as response:
            body = __import__("json").loads(response.read().decode("utf-8", errors="replace"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return []

    vulns = body.get("vulns") or []
    results: list[dict] = []
    for vuln in vulns:
        cve_id = next((alias for alias in vuln.get("aliases", []) if alias.startswith("CVE-")), None)
        severity = None
        for item in vuln.get("severity") or []:
            if item.get("type") == "CVSS_V3":
                try:
                    severity = float(item.get("score"))
                except (TypeError, ValueError):
                    pass
        results.append(
            {
                "id": vuln.get("id"),
                "cve_id": cve_id,
                "summary": vuln.get("summary") or vuln.get("details"),
                "cvss": severity,
            }
        )
    return results
