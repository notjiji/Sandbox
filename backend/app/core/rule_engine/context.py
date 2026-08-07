"""Build evaluation context from parsed scanner data."""

from __future__ import annotations

from typing import Any

from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.utils import header_lookup


def build_context(parsed: Any, asset: ScanTarget, *, plugin_id: str) -> dict[str, Any]:
    """Flatten parsed data and asset fields into a rule evaluation context."""
    if hasattr(parsed, "model_dump"):
        context: dict[str, Any] = parsed.model_dump(mode="python")
    elif isinstance(parsed, dict):
        context = dict(parsed)
    else:
        context = {"value": parsed}

    context["identifier"] = asset.identifier
    context["asset_id"] = asset.asset_id
    context["asset_type"] = asset.asset_type
    context["plugin_id"] = plugin_id

    enricher = _CONTEXT_ENRICHERS.get(plugin_id)
    if enricher is not None:
        context.update(enricher(parsed, asset))

    return context


def _http_headers_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    exposed: list[str] = []
    if getattr(parsed, "server", None):
        exposed.append(f"Server: {parsed.server}")
    if getattr(parsed, "powered_by", None):
        exposed.append(f"X-Powered-By: {parsed.powered_by}")

    weak_cookies = getattr(parsed, "weak_cookies", []) or []
    cookie_details: list[str] = []
    for cookie in weak_cookies:
        issues: list[str] = []
        if not cookie.secure:
            issues.append("missing Secure")
        if not cookie.httponly:
            issues.append("missing HttpOnly")
        if cookie.samesite and cookie.samesite.lower() == "none" and not cookie.secure:
            issues.append("SameSite=None without Secure")
        cookie_details.append(f"Cookie '{cookie.name}': {', '.join(issues) or 'weak configuration'}")

    mixed = getattr(parsed, "mixed_content_urls", []) or []
    redirect_issues = getattr(parsed, "redirect_chain_issues", []) or []
    csp_issues: list[str] = []
    if getattr(parsed, "csp_has_unsafe_inline", False):
        csp_issues.append("unsafe-inline")
    if getattr(parsed, "csp_has_unsafe_eval", False):
        csp_issues.append("unsafe-eval")
    if getattr(parsed, "csp_has_wildcard", False):
        csp_issues.append("wildcard source")

    broad_csp: list[str] = []
    if getattr(parsed, "csp_has_data_uri", False):
        broad_csp.append("data:")
    if getattr(parsed, "csp_has_blob_uri", False):
        broad_csp.append("blob:")
    if getattr(parsed, "csp_has_broad_https", False):
        broad_csp.append("https:")

    return {
        "server_exposed": bool(getattr(parsed, "server_exposed", False) or getattr(parsed, "server", None) or getattr(parsed, "powered_by", None)),
        "server_exposed_evidence": "; ".join(exposed),
        "weak_cookies_evidence": "; ".join(cookie_details),
        "mixed_content_evidence": ", ".join(mixed[:3]),
        "redirect_chain_evidence": "; ".join(redirect_issues),
        "weak_csp_evidence": ", ".join(csp_issues),
        "broad_csp_evidence": ", ".join(broad_csp),
        "hsts_weak_evidence": f"HSTS max-age={getattr(parsed, 'hsts_max_age', None)} (recommended >= 15552000)",
        "trace_evidence": f"TRACE request to {getattr(parsed, 'final_url', asset.identifier)} was accepted",
        "access_control_allow_origin": header_lookup(getattr(parsed, "headers", {}) or {}, "access-control-allow-origin"),
        "cors_credentials_with_wildcard": _cors_credentials_with_wildcard(parsed),
        "api_schema_evidence": ", ".join(getattr(parsed, "api_schema_paths", []) or [])[:200],
    }


def _cors_credentials_with_wildcard(parsed: Any) -> bool:
    headers = getattr(parsed, "headers", {}) or {}
    origin = header_lookup(headers, "access-control-allow-origin")
    credentials = header_lookup(headers, "access-control-allow-credentials")
    return bool(origin and origin.strip() == "*" and credentials and credentials.lower() == "true")


def _dns_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    spf_records = getattr(parsed, "spf_records", []) or []
    takeover = getattr(parsed, "subdomain_takeover_risks", []) or []
    mx_bad = getattr(parsed, "mx_misconfigured", []) or []
    resolver = getattr(parsed, "resolver_discrepancies", []) or []
    return {
        "spf_record_count": len(spf_records),
        "subdomain_takeover_evidence": "; ".join(takeover),
        "mx_misconfigured_evidence": ", ".join(mx_bad),
        "resolver_discrepancy_evidence": "; ".join(resolver),
    }


def _ssl_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    cert = getattr(parsed, "certificate", None)
    weak_rsa = False
    weak_sig = False
    incomplete_san = False
    incomplete_parts: list[str] = []
    sans_evidence = "none"
    if cert is not None:
        if getattr(cert, "public_key_algorithm", None) == "RSA":
            bits = getattr(cert, "public_key_bits", None)
            weak_rsa = bits is not None and bits < 2048
        algorithm = (getattr(cert, "signature_algorithm", None) or "").lower()
        weak_sig = any(token in algorithm for token in ("md5", "sha1"))
        sans = getattr(cert, "sans", []) or []
        sans_evidence = ", ".join(sans) or getattr(cert, "common_name", None) or "none"
        if not getattr(parsed, "san_covers_apex", True):
            incomplete_parts.append("apex")
        if not getattr(parsed, "san_covers_www", True):
            incomplete_parts.append("www")
        incomplete_san = bool(incomplete_parts)
    weak_ciphers = getattr(parsed, "weak_ciphers_accepted", []) or []
    suspicious = getattr(parsed, "suspicious_ct_issuers", []) or []
    return {
        "weak_rsa_key": weak_rsa,
        "weak_signature": weak_sig,
        "incomplete_san_coverage": incomplete_san,
        "incomplete_san_evidence": ", ".join(incomplete_parts),
        "certificate_sans_evidence": sans_evidence,
        "weak_ciphers_evidence": ", ".join(weak_ciphers),
        "suspicious_ct_issuers_evidence": ", ".join(suspicious[:3]),
    }


def _ports_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    open_ports = getattr(parsed, "open_ports", []) or []
    context: dict[str, Any] = {"open_ports": open_ports}
    for service in getattr(parsed, "services", []) or []:
        if not getattr(service, "open", False):
            continue
        parts = [f"TCP/{service.port} open"]
        if getattr(service, "product", None):
            parts.append(service.product)
        if getattr(service, "version", None):
            parts.append(service.version)
        elif getattr(service, "banner", None) and not getattr(service, "product", None):
            parts.append(str(service.banner)[:120])
        context[f"port_{service.port}_evidence"] = " — ".join(parts)
    return context


def _whois_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    expires = getattr(parsed, "expires", None)
    return {
        "expires_evidence": expires.isoformat() if expires is not None else "unknown",
    }


def _tls_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    legacy = [item for item in getattr(parsed, "legacy_protocols_accepted", []) or []]
    weak = getattr(parsed, "weak_ciphers_accepted", []) or []
    return {
        "legacy_protocol_enabled": bool(legacy),
        "legacy_protocols_evidence": ", ".join(legacy),
        "weak_ciphers_evidence": ", ".join(weak),
    }


def _robots_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    def _format_paths(paths: list[str], *, limit: int = 5) -> str:
        shown = paths[:limit]
        suffix = f" (+{len(paths) - limit} more)" if len(paths) > limit else ""
        return ", ".join(shown) + suffix

    admin_paths = getattr(parsed, "admin_paths", []) or []
    debug_paths = getattr(parsed, "debug_paths", []) or []
    sensitive_paths = getattr(parsed, "sensitive_paths", []) or []
    return {
        "admin_paths_evidence": _format_paths(admin_paths),
        "debug_paths_evidence": _format_paths(debug_paths),
        "sensitive_paths_evidence": _format_paths(sensitive_paths),
    }


def _security_txt_enricher(parsed: Any, asset: ScanTarget) -> dict[str, Any]:
    contacts = getattr(parsed, "contacts", []) or []
    encryption = getattr(parsed, "encryption", []) or []
    canonical = getattr(parsed, "canonical", []) or []
    return {
        "invalid_contacts_evidence": ", ".join(contacts[:3]),
        "invalid_encryption_evidence": ", ".join(encryption[:3]),
        "canonical_evidence": (
            f"Canonical URI is invalid or does not match the downloaded security.txt location: {canonical[0]}"
            if canonical
            else "Canonical URI is invalid or does not match the downloaded security.txt location"
        ),
        "expires_evidence": f"Expires field is in the past: {getattr(parsed, 'expires', '')}",
    }


_CONTEXT_ENRICHERS = {
    "http_headers": _http_headers_enricher,
    "robots": _robots_enricher,
    "security_txt": _security_txt_enricher,
    "dns": _dns_enricher,
    "ssl": _ssl_enricher,
    "ports": _ports_enricher,
    "whois": _whois_enricher,
    "tls": _tls_enricher,
}
