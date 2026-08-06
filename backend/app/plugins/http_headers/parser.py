"""Convert raw HTTP responses into structured objects."""

from urllib.parse import urlparse

from app.plugins.http_headers.schemas import (
    HttpHeadersParsedData,
    HttpHeadersRawResponse,
    ParsedCookie,
    SecurityHeaders,
)
from app.plugins.http_headers.utils import (
    analyze_csp,
    analyze_hsts,
    analyze_redirect_chain,
    find_mixed_content,
    header_lookup,
    is_session_like_cookie,
    redirect_targets_https,
)


def _parse_cookies(raw) -> list[ParsedCookie]:
    return [
        ParsedCookie(
            name=cookie.name,
            secure=cookie.secure,
            httponly=cookie.httponly,
            samesite=cookie.samesite,
            is_session_like=is_session_like_cookie(cookie.name),
        )
        for cookie in raw.cookies
    ]


def _detect_weak_cookies(cookies: list[ParsedCookie], *, is_https: bool) -> list[ParsedCookie]:
    weak: list[ParsedCookie] = []
    for cookie in cookies:
        if not cookie.is_session_like:
            continue
        if is_https and not cookie.secure:
            weak.append(cookie)
            continue
        if not cookie.httponly:
            weak.append(cookie)
            continue
        if cookie.samesite and cookie.samesite.lower() == "none" and not cookie.secure:
            weak.append(cookie)
    return weak


def _http_redirects_to_https(raw: HttpHeadersRawResponse) -> bool | None:
    if raw.http_probe is None:
        return None

    if raw.http_probe.status_code in {301, 302, 303, 307, 308}:
        location = header_lookup(raw.http_probe.headers, "location")
        return redirect_targets_https(location)

    if raw.http_probe.final_url.startswith("https://"):
        return True

    return False


def parse(raw: HttpHeadersRawResponse) -> HttpHeadersParsedData:
    probe = raw.primary
    headers = probe.headers
    csp = header_lookup(headers, "content-security-policy")
    hsts = header_lookup(headers, "strict-transport-security")
    csp_unsafe_inline, csp_unsafe_eval, csp_wildcard = analyze_csp(csp)
    hsts_max_age, hsts_subdomains, hsts_preload, hsts_weak = analyze_hsts(hsts)

    security = SecurityHeaders(
        content_security_policy=csp,
        strict_transport_security=hsts,
        referrer_policy=header_lookup(headers, "referrer-policy"),
        x_frame_options=header_lookup(headers, "x-frame-options"),
        x_content_type_options=header_lookup(headers, "x-content-type-options"),
        permissions_policy=header_lookup(headers, "permissions-policy")
        or header_lookup(headers, "feature-policy"),
    )
    cookies = _parse_cookies(probe)
    is_https = urlparse(probe.final_url).scheme == "https"
    trace_enabled = bool(raw.trace_probe and raw.trace_probe.allowed)
    redirect_issues, open_redirect = analyze_redirect_chain(probe.redirects, is_https_start=is_https)
    mixed = find_mixed_content(probe.body, is_https=is_https)
    security_txt_present = bool(
        raw.security_txt_probe
        and raw.security_txt_probe.status_code == 200
        and "contact" in raw.security_txt_probe.body.lower()
    )

    return HttpHeadersParsedData(
        url=probe.url,
        final_url=probe.final_url,
        status_code=probe.status_code,
        headers=headers,
        server=header_lookup(headers, "server"),
        powered_by=header_lookup(headers, "x-powered-by"),
        content_type=probe.content_type,
        cookies=cookies,
        redirects=probe.redirects,
        security_headers=security,
        timing=probe.timing,
        body_length=probe.body_length,
        is_https=is_https,
        http_redirects_to_https=_http_redirects_to_https(raw),
        trace_enabled=trace_enabled,
        weak_cookies=_detect_weak_cookies(cookies, is_https=is_https),
        csp_has_unsafe_inline=csp_unsafe_inline,
        csp_has_unsafe_eval=csp_unsafe_eval,
        csp_has_wildcard=csp_wildcard,
        hsts_max_age=hsts_max_age,
        hsts_includes_subdomains=hsts_subdomains,
        hsts_preload=hsts_preload,
        hsts_is_weak=hsts_weak,
        mixed_content_urls=mixed,
        redirect_chain_issues=redirect_issues,
        security_txt_present=security_txt_present,
        open_redirect_candidate=open_redirect,
    )
