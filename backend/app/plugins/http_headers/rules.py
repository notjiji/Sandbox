"""Independent HTTP security rules — each rule stands alone."""

from collections.abc import Callable

from app.findings.enums import FindingSeverity
from app.plugins.base.contracts import FindingCheckStatus, ScanFinding, scan_finding
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.schemas import HttpHeadersParsedData, ParsedCookie

RuleFn = Callable[[HttpHeadersParsedData, ScanTarget, str], ScanFinding | None]


def _missing_header_finding(
    *,
    plugin_id: str,
    asset: ScanTarget,
    rule_id: str,
    title: str,
    header_name: str,
    severity: FindingSeverity,
    recommendation: str,
    reference_links: list[str] | None = None,
) -> ScanFinding:
    return scan_finding(
        plugin=plugin_id,
        rule_id=rule_id,
        asset_id=asset.asset_id,
        title=title,
        description=f"The {header_name} response header was not present.",
        category="headers",
        evidence=f"{header_name} header not present on {asset.identifier}",
        recommendation=recommendation,
        reference_links=reference_links or [],
        severity=severity,
        status=FindingCheckStatus.FAILED,
    )


def rule_missing_csp(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.has_csp:
        return None
    return _missing_header_finding(
        plugin_id=plugin_id,
        asset=asset,
        rule_id="HTTP_NO_CSP",
        title="Missing Content Security Policy",
        header_name="Content-Security-Policy",
        severity=FindingSeverity.HIGH,
        recommendation=(
            "Define a Content-Security-Policy that restricts script, style, and resource origins. "
            "Start with report-only mode, then enforce."
        ),
        reference_links=[
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/CSP",
            "https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html",
        ],
    )


def rule_missing_hsts(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.has_hsts or not parsed.is_https:
        return None
    return _missing_header_finding(
        plugin_id=plugin_id,
        asset=asset,
        rule_id="HTTP_NO_HSTS",
        title="Missing Strict Transport Security",
        header_name="Strict-Transport-Security",
        severity=FindingSeverity.HIGH,
        recommendation=(
            "Add Strict-Transport-Security with a long max-age (e.g. max-age=31536000; includeSubDomains; preload)."
        ),
        reference_links=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Strict-Transport-Security"],
    )


def rule_missing_referrer_policy(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if parsed.has_referrer_policy:
        return None
    return _missing_header_finding(
        plugin_id=plugin_id,
        asset=asset,
        rule_id="HTTP_NO_REFERRER_POLICY",
        title="Missing Referrer Policy",
        header_name="Referrer-Policy",
        severity=FindingSeverity.MEDIUM,
        recommendation="Set Referrer-Policy to strict-origin-when-cross-origin or no-referrer as appropriate.",
        reference_links=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Referrer-Policy"],
    )


def rule_missing_x_frame_options(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if parsed.has_x_frame_options:
        return None
    return _missing_header_finding(
        plugin_id=plugin_id,
        asset=asset,
        rule_id="HTTP_NO_X_FRAME_OPTIONS",
        title="Missing X-Frame-Options",
        header_name="X-Frame-Options",
        severity=FindingSeverity.MEDIUM,
        recommendation="Set X-Frame-Options to DENY or SAMEORIGIN, or use CSP frame-ancestors.",
        reference_links=["https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Frame-Options"],
    )


def rule_server_header_exposed(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if not parsed.server_exposed:
        return None

    exposed = []
    if parsed.server:
        exposed.append(f"Server: {parsed.server}")
    if parsed.powered_by:
        exposed.append(f"X-Powered-By: {parsed.powered_by}")

    return scan_finding(
        plugin=plugin_id,
        rule_id="HTTP_SERVER_HEADER_EXPOSED",
        asset_id=asset.asset_id,
        title="Server Technology Header Exposed",
        description="The response reveals server or framework identifiers that aid fingerprinting.",
        category="headers",
        evidence="; ".join(exposed),
        recommendation="Remove or genericize Server and X-Powered-By headers at the reverse proxy or application layer.",
        reference_links=["https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/01-Information_Gathering/02-Fingerprint_Web_Server"],
        severity=FindingSeverity.LOW,
        status=FindingCheckStatus.WARNING,
    )


def rule_trace_enabled(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.trace_enabled:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="HTTP_TRACE_ENABLED",
        asset_id=asset.asset_id,
        title="HTTP TRACE Method Enabled",
        description="The server responded to a TRACE request, which can expose cookies and auth headers via cross-site tracing.",
        category="headers",
        evidence=f"TRACE request to {parsed.final_url} was accepted",
        recommendation="Disable TRACE and TRACK methods in the web server configuration.",
        reference_links=["https://owasp.org/www-community/attacks/Cross_Site_Tracing"],
        severity=FindingSeverity.MEDIUM,
        status=FindingCheckStatus.FAILED,
    )


def rule_no_https_redirect(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if parsed.http_redirects_to_https is not False:
        return None
    return scan_finding(
        plugin=plugin_id,
        rule_id="HTTP_NO_HTTPS_REDIRECT",
        asset_id=asset.asset_id,
        title="HTTP Does Not Redirect to HTTPS",
        description="Plain HTTP is served without redirecting clients to HTTPS.",
        category="transport",
        evidence=f"HTTP request to {asset.identifier} did not redirect to HTTPS",
        recommendation="Configure an automatic 301/302 redirect from HTTP to HTTPS for all paths.",
        reference_links=["https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html"],
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def _weak_cookie_detail(cookie: ParsedCookie) -> str:
    issues = []
    if not cookie.secure:
        issues.append("missing Secure")
    if not cookie.httponly:
        issues.append("missing HttpOnly")
    if cookie.samesite and cookie.samesite.lower() == "none" and not cookie.secure:
        issues.append("SameSite=None without Secure")
    return f"Cookie '{cookie.name}': {', '.join(issues) or 'weak configuration'}"


def rule_weak_cookies(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.weak_cookies:
        return None

    evidence = "; ".join(_weak_cookie_detail(cookie) for cookie in parsed.weak_cookies)
    return scan_finding(
        plugin=plugin_id,
        rule_id="HTTP_WEAK_COOKIE",
        asset_id=asset.asset_id,
        title="Weak Session Cookie Configuration",
        description="One or more session-like cookies lack recommended security attributes.",
        category="cookies",
        evidence=evidence,
        recommendation=(
            "Set Secure and HttpOnly on session cookies. Use SameSite=Lax or Strict; "
            "if SameSite=None is required, also set Secure."
        ),
        reference_links=[
            "https://owasp.org/www-community/HttpOnly",
            "https://developer.mozilla.org/en-US/docs/Web/HTTP/Cookies",
        ],
        severity=FindingSeverity.HIGH,
        status=FindingCheckStatus.FAILED,
    )


def rule_missing_x_content_type_options(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if parsed.has_x_content_type_options:
        return None
    return _missing_header_finding(
        plugin_id=plugin_id, asset=asset, rule_id="HTTP_NO_X_CONTENT_TYPE_OPTIONS",
        title="Missing X-Content-Type-Options", header_name="X-Content-Type-Options",
        severity=FindingSeverity.MEDIUM,
        recommendation='Set X-Content-Type-Options: nosniff to prevent MIME-type sniffing.',
    )


def rule_missing_permissions_policy(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if parsed.has_permissions_policy:
        return None
    return _missing_header_finding(
        plugin_id=plugin_id, asset=asset, rule_id="HTTP_NO_PERMISSIONS_POLICY",
        title="Missing Permissions-Policy", header_name="Permissions-Policy",
        severity=FindingSeverity.LOW,
        recommendation="Restrict browser features via Permissions-Policy header.",
    )


def rule_weak_csp(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.has_csp:
        return None
    issues = []
    if parsed.csp_has_unsafe_inline:
        issues.append("unsafe-inline")
    if parsed.csp_has_unsafe_eval:
        issues.append("unsafe-eval")
    if parsed.csp_has_wildcard:
        issues.append("wildcard source")
    if not issues:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="HTTP_WEAK_CSP", asset_id=asset.asset_id,
        title="Weak Content Security Policy", category="headers",
        evidence=f"CSP contains: {', '.join(issues)}",
        recommendation="Remove unsafe-inline, unsafe-eval, and wildcard directives where possible.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_csp_broad_sources(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.has_csp:
        return None
    issues = []
    if parsed.csp_has_data_uri:
        issues.append("data:")
    if parsed.csp_has_blob_uri:
        issues.append("blob:")
    if parsed.csp_has_broad_https:
        issues.append("https:")
    if not issues:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="HTTP_CSP_BROAD_SOURCES", asset_id=asset.asset_id,
        title="Overly Broad CSP Sources", category="headers",
        evidence=f"CSP allows broad sources: {', '.join(issues)}",
        recommendation="Avoid data:, blob:, and scheme-wide https: in script/default directives.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_weak_hsts(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.has_hsts or not parsed.hsts_is_weak:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="HTTP_WEAK_HSTS", asset_id=asset.asset_id,
        title="Weak HSTS Configuration", category="headers",
        evidence=f"HSTS max-age={parsed.hsts_max_age} (recommended >= 15552000)",
        recommendation="Set max-age to at least 180 days; add includeSubDomains and preload if eligible.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_mixed_content(parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str) -> ScanFinding | None:
    if not parsed.mixed_content_urls:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="HTTP_MIXED_CONTENT", asset_id=asset.asset_id,
        title="Mixed Content Detected", category="headers",
        evidence=f"HTTP resources on HTTPS page: {', '.join(parsed.mixed_content_urls[:3])}",
        recommendation="Serve all resources over HTTPS.",
        severity=FindingSeverity.MEDIUM, status=FindingCheckStatus.FAILED,
    )


def rule_insecure_redirect_chain(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if not parsed.redirect_chain_issues:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="HTTP_INSECURE_REDIRECT", asset_id=asset.asset_id,
        title="Insecure Redirect Chain", category="transport",
        evidence="; ".join(parsed.redirect_chain_issues),
        recommendation="Ensure redirects never downgrade from HTTPS to HTTP.",
        severity=FindingSeverity.HIGH, status=FindingCheckStatus.FAILED,
    )


def rule_missing_security_txt(
    parsed: HttpHeadersParsedData, asset: ScanTarget, plugin_id: str
) -> ScanFinding | None:
    if parsed.security_txt_present:
        return None
    return scan_finding(
        plugin=plugin_id, rule_id="HTTP_MISSING_SECURITY_TXT", asset_id=asset.asset_id,
        title="Missing security.txt", category="exposure",
        evidence="/.well-known/security.txt not found or invalid",
        recommendation="Publish a security.txt with contact and disclosure policy per RFC 9116.",
        reference_links=["https://securitytxt.org/"],
        severity=FindingSeverity.LOW, status=FindingCheckStatus.WARNING,
    )


RULES: list[RuleFn] = [
    rule_missing_csp,
    rule_weak_csp,
    rule_csp_broad_sources,
    rule_missing_hsts,
    rule_weak_hsts,
    rule_missing_referrer_policy,
    rule_missing_x_frame_options,
    rule_missing_x_content_type_options,
    rule_missing_permissions_policy,
    rule_server_header_exposed,
    rule_trace_enabled,
    rule_no_https_redirect,
    rule_insecure_redirect_chain,
    rule_mixed_content,
    rule_weak_cookies,
    rule_missing_security_txt,
]


def evaluate_rules(parsed: HttpHeadersParsedData, asset: ScanTarget, *, plugin_id: str) -> list[ScanFinding]:
    findings: list[ScanFinding] = []
    for rule in RULES:
        finding = rule(parsed, asset, plugin_id)
        if finding is not None:
            findings.append(finding)
    return findings
