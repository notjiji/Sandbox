from app.plugins.base.plugin import ScanTarget
from app.plugins.fingerprint import parser, rules
from app.plugins.fingerprint.plugin import FingerprintPlugin
from app.plugins.fingerprint.schemas import FingerprintCookieRaw, FingerprintRawResponse


def test_detects_wordpress_from_html_and_scripts() -> None:
    raw = FingerprintRawResponse(
        url="https://blog.example.com",
        final_url="https://blog.example.com/",
        status_code=200,
        headers={"Server": "nginx"},
        cookies=[FingerprintCookieRaw(name="wordpress_logged_in_abc", value="1")],
        body='<meta name="generator" content="WordPress 6.4" />',
        script_srcs=["/wp-content/themes/twentytwenty/style.js"],
    )

    parsed = parser.parse(raw)
    names = {tech.name for tech in parsed.technologies}

    assert "WordPress" in names
    assert "Nginx" in names


def test_detects_react_nextjs_cloudflare_php_laravel() -> None:
    raw = FingerprintRawResponse(
        url="https://app.example.com",
        final_url="https://app.example.com/",
        status_code=200,
        headers={
            "Server": "cloudflare",
            "CF-RAY": "abc123",
            "X-Powered-By": "PHP/8.2",
        },
        cookies=[
            FingerprintCookieRaw(name="laravel_session", value="abc"),
            FingerprintCookieRaw(name="XSRF-TOKEN", value="token"),
            FingerprintCookieRaw(name="PHPSESSID", value="sess"),
        ],
        body='<script id="__NEXT_DATA__" type="application/json">{}</script><div id="__next"></div>',
        script_srcs=[
            "/_next/static/chunks/main.js",
            "https://cdn.example.com/react-dom.production.min.js",
        ],
    )

    parsed = parser.parse(raw)
    names = {tech.name for tech in parsed.technologies}

    assert {"React", "Next.js", "Cloudflare", "PHP", "Laravel"}.issubset(names)


def test_detects_apache_from_server_header() -> None:
    raw = FingerprintRawResponse(
        url="https://legacy.example.com",
        final_url="https://legacy.example.com/",
        status_code=200,
        headers={"Server": "Apache/2.4.57 (Ubuntu)"},
        cookies=[],
        body="",
        script_srcs=[],
    )

    parsed = parser.parse(raw)
    assert any(tech.name == "Apache" for tech in parsed.technologies)


def test_rules_emit_no_findings() -> None:
    raw = FingerprintRawResponse(
        url="https://example.com",
        final_url="https://example.com/",
        status_code=200,
        headers={"Server": "nginx"},
        cookies=[],
        body="",
        script_srcs=[],
    )
    parsed = parser.parse(raw)
    asset = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")

    assert rules.evaluate_rules(parsed, asset, plugin_id="fingerprint") == []


def test_build_metadata_includes_technologies() -> None:
    plugin = FingerprintPlugin()
    raw = FingerprintRawResponse(
        url="https://example.com",
        final_url="https://example.com/",
        status_code=200,
        headers={"Server": "nginx", "X-Powered-By": "PHP/8.2"},
        cookies=[FingerprintCookieRaw(name="PHPSESSID", value="abc")],
        body="",
        script_srcs=[],
    )
    parsed = parser.parse(raw)
    metadata = plugin.build_metadata(parsed)

    assert metadata["technology_count"] >= 2
    assert metadata["headers"]["server"] == "nginx"
    assert any(item["name"] == "PHP" for item in metadata["technologies"])
