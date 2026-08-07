"""Build evaluation context from parsed scanner data."""

from __future__ import annotations

from typing import Any

from app.plugins.base.plugin import ScanTarget


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
}
