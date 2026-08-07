"""Technology detection signatures for headers, HTML, scripts, and cookies."""

from __future__ import annotations

import re

from app.plugins.fingerprint.schemas import DetectedTechnology

_HEADER_CHECKS: list[tuple[str, str, str, float, str]] = [
    ("server", r"nginx", "Nginx", "server", 0.95, "Server header"),
    ("server", r"apache", "Apache", "server", 0.95, "Server header"),
    ("server", r"cloudflare", "Cloudflare", "cdn", 0.95, "Server header"),
    ("server", r"microsoft-iis", "Microsoft IIS", "server", 0.95, "Server header"),
    ("server", r"openresty", "OpenResty", "server", 0.9, "Server header"),
    ("server", r"awselb", "AWS ELB", "load_balancer", 0.9, "Server header"),
    ("x-powered-by", r"php", "PHP", "language", 0.9, "X-Powered-By header"),
    ("x-powered-by", r"next\.js", "Next.js", "framework", 0.95, "X-Powered-By header"),
    ("x-powered-by", r"express", "Express", "framework", 0.85, "X-Powered-By header"),
    ("x-powered-by", r"asp\.net", "ASP.NET", "framework", 0.9, "X-Powered-By header"),
    ("x-powered-by", r"drupal", "Drupal", "cms", 0.9, "X-Powered-By header"),
    ("x-generator", r"wordpress", "WordPress", "cms", 0.9, "X-Generator header"),
    ("x-drupal-cache", r".+", "Drupal", "cms", 0.85, "X-Drupal-Cache header"),
    ("x-shopify-stage", r".+", "Shopify", "platform", 0.95, "X-Shopify-Stage header"),
    ("x-vercel-id", r".+", "Vercel", "platform", 0.95, "X-Vercel-Id header"),
    ("x-netlify", r".+", "Netlify", "platform", 0.9, "X-Netlify header"),
    ("cf-ray", r".+", "Cloudflare", "cdn", 0.98, "CF-RAY header"),
    ("cf-cache-status", r".+", "Cloudflare", "cdn", 0.9, "CF-Cache-Status header"),
    ("x-served-by", r"fastly", "Fastly", "cdn", 0.9, "X-Served-By header"),
    ("x-cache", r".+", "CDN", "cdn", 0.6, "X-Cache header"),
    ("via", r"cloudfront", "Amazon CloudFront", "cdn", 0.95, "Via header"),
    ("x-amz-cf-id", r".+", "Amazon CloudFront", "cdn", 0.95, "X-Amz-Cf-Id header"),
    ("x-azure-ref", r".+", "Azure Front Door", "cdn", 0.9, "X-Azure-Ref header"),
    ("x-sucuri-id", r".+", "Sucuri WAF", "waf", 0.95, "X-Sucuri-Id header"),
    ("x-sucuri-cache", r".+", "Sucuri WAF", "waf", 0.9, "X-Sucuri-Cache header"),
    ("server", r"sucuri", "Sucuri WAF", "waf", 0.9, "Server header"),
    ("x-cdn", r"incapsula", "Imperva Incapsula", "waf", 0.95, "X-CDN header"),
    ("x-iinfo", r".+", "Imperva Incapsula", "waf", 0.85, "X-Iinfo header"),
    ("x-akamai-transformed", r".+", "Akamai", "cdn", 0.95, "X-Akamai-Transformed header"),
    ("x-firewall-protection", r".+", "WAF", "waf", 0.7, "X-Firewall-Protection header"),
]

_COOKIE_CHECKS: list[tuple[str, str, str, float, str]] = [
    (r"phpsessid", "PHP", "language", 0.9, "PHPSESSID cookie"),
    (r"laravel_session", "Laravel", "framework", 0.95, "laravel_session cookie"),
    (r"xsrf-token", "Laravel", "framework", 0.7, "XSRF-TOKEN cookie"),
    (r"__cf_bm|__cfduid|cf_clearance", "Cloudflare", "cdn", 0.9, "Cloudflare cookie"),
    (r"wordpress_", "WordPress", "cms", 0.85, "WordPress cookie"),
    (r"wp-settings", "WordPress", "cms", 0.85, "WordPress settings cookie"),
    (r"_shopify", "Shopify", "platform", 0.9, "Shopify cookie"),
    (r"django", "Django", "framework", 0.85, "Django cookie"),
    (r"rack.session", "Ruby on Rails", "framework", 0.85, "Rails session cookie"),
    (r"jsessionid", "Java", "language", 0.8, "JSESSIONID cookie"),
]

_SCRIPT_CHECKS: list[tuple[str, str, str, float, str]] = [
    (r"/wp-content/", "WordPress", "cms", 0.9, "wp-content script path"),
    (r"/wp-includes/", "WordPress", "cms", 0.9, "wp-includes script path"),
    (r"/_next/static/", "Next.js", "framework", 0.95, "_next/static script path"),
    (r"react(?:\.production|\.development)?(?:\.min)?\.js", "React", "framework", 0.9, "React script"),
    (r"react-dom", "React", "framework", 0.9, "React DOM script"),
    (r"next/dist", "Next.js", "framework", 0.9, "Next.js bundle"),
    (r"vue(?:\.runtime)?(?:\.min)?\.js", "Vue.js", "framework", 0.9, "Vue script"),
    (r"angular(?:\.min)?\.js", "Angular", "framework", 0.9, "Angular script"),
    (r"jquery(?:-\[\d.]+)?(?:\.min)?\.js", "jQuery", "library", 0.85, "jQuery script"),
    (r"bootstrap(?:\.min)?\.js", "Bootstrap", "library", 0.85, "Bootstrap script"),
    (r"cdn\.shopify\.com", "Shopify", "platform", 0.95, "Shopify CDN script"),
    (r"gatsby", "Gatsby", "framework", 0.85, "Gatsby script"),
    (r"htmx", "htmx", "library", 0.85, "htmx script"),
]

_HTML_CHECKS: list[tuple[str, str, str, float, str]] = [
    (r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']WordPress', "WordPress", "cms", 0.95, "generator meta tag"),
    (r"/wp-content/", "WordPress", "cms", 0.85, "wp-content in HTML"),
    (r"/wp-includes/", "WordPress", "cms", 0.85, "wp-includes in HTML"),
    (r"__NEXT_DATA__", "Next.js", "framework", 0.95, "__NEXT_DATA__ payload"),
    (r'data-reactroot|data-reactid|__REACT_DEVTOOLS_GLOBAL_HOOK__', "React", "framework", 0.85, "React DOM markers"),
    (r'id=["\']__next["\']', "Next.js", "framework", 0.8, "__next root element"),
    (r"https://api\.w\.org/", "WordPress", "cms", 0.8, "WordPress REST API link"),
    (r"cdn\.shopify\.com", "Shopify", "platform", 0.9, "Shopify CDN reference"),
    (r"data-drupal-selector", "Drupal", "cms", 0.9, "Drupal data attribute"),
    (r"Joomla!", "Joomla", "cms", 0.9, "Joomla marker"),
    (r"webpackJsonp|__webpack_require__", "Webpack", "build", 0.75, "Webpack runtime"),
    (r"vite", "Vite", "build", 0.7, "Vite marker"),
]


def _header_lookup(headers: dict[str, str], name: str) -> str | None:
    target = name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def _add(
    found: dict[str, DetectedTechnology],
    *,
    name: str,
    category: str,
    confidence: float,
    evidence: str,
    source: str,
) -> None:
    existing = found.get(name)
    if existing is None or confidence > existing.confidence:
        found[name] = DetectedTechnology(
            name=name,
            category=category,
            confidence=confidence,
            evidence=evidence,
            source=source,
        )


def detect_from_headers(headers: dict[str, str]) -> list[DetectedTechnology]:
    found: dict[str, DetectedTechnology] = {}
    for header_name, pattern, tech_name, category, confidence, evidence_label in _HEADER_CHECKS:
        value = _header_lookup(headers, header_name)
        if value and re.search(pattern, value, re.IGNORECASE):
            _add(
                found,
                name=tech_name,
                category=category,
                confidence=confidence,
                evidence=f"{evidence_label}: {value[:120]}",
                source="header",
            )
    return list(found.values())


def detect_from_cookies(cookie_names: list[str]) -> list[DetectedTechnology]:
    found: dict[str, DetectedTechnology] = {}
    joined = " ".join(cookie_names).lower()
    for pattern, tech_name, category, confidence, evidence in _COOKIE_CHECKS:
        if re.search(pattern, joined, re.IGNORECASE):
            _add(
                found,
                name=tech_name,
                category=category,
                confidence=confidence,
                evidence=evidence,
                source="cookie",
            )
    return list(found.values())


def detect_from_scripts(script_srcs: list[str]) -> list[DetectedTechnology]:
    found: dict[str, DetectedTechnology] = {}
    joined = " ".join(script_srcs)
    for pattern, tech_name, category, confidence, evidence in _SCRIPT_CHECKS:
        if re.search(pattern, joined, re.IGNORECASE):
            _add(
                found,
                name=tech_name,
                category=category,
                confidence=confidence,
                evidence=evidence,
                source="script",
            )
    return list(found.values())


def detect_from_html(body: str) -> list[DetectedTechnology]:
    found: dict[str, DetectedTechnology] = {}
    if not body:
        return []
    for pattern, tech_name, category, confidence, evidence in _HTML_CHECKS:
        if re.search(pattern, body, re.IGNORECASE):
            _add(
                found,
                name=tech_name,
                category=category,
                confidence=confidence,
                evidence=evidence,
                source="html",
            )
    return list(found.values())


def merge_technologies(*groups: list[DetectedTechnology]) -> list[DetectedTechnology]:
    merged: dict[str, DetectedTechnology] = {}
    for group in groups:
        for tech in group:
            existing = merged.get(tech.name)
            if existing is None or tech.confidence > existing.confidence:
                merged[tech.name] = tech
    return sorted(merged.values(), key=lambda item: (-item.confidence, item.name))
