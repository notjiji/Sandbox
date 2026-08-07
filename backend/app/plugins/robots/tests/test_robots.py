from app.plugins.base.plugin import ScanTarget
from app.plugins.robots import parser, rules
from app.plugins.robots.plugin import RobotsPlugin
from app.plugins.robots.schemas import RobotsRawResponse


ROBOTS_SAMPLE = """\
User-agent: *
Disallow: /admin/
Disallow: /private/
Disallow: /debug/
Allow: /public/
Disallow: /wp-admin/

User-agent: Googlebot
Disallow: /internal/

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
"""


def test_parse_disallow_allow_sitemap() -> None:
    raw = RobotsRawResponse(url="https://example.com/robots.txt", status_code=200, body=ROBOTS_SAMPLE)
    parsed = parser.parse(raw)

    assert parsed.present is True
    assert len(parsed.disallowed_paths) == 5
    assert len(parsed.allowed_paths) == 1
    assert parsed.allowed_paths[0].path == "/public/"
    assert parsed.sitemaps == [
        "https://example.com/sitemap.xml",
        "https://example.com/sitemap-news.xml",
    ]
    assert "*" in parsed.user_agents
    assert "Googlebot" in parsed.user_agents


def test_detects_admin_debug_sensitive_paths() -> None:
    raw = RobotsRawResponse(url="https://example.com/robots.txt", status_code=200, body=ROBOTS_SAMPLE)
    parsed = parser.parse(raw)

    assert "/admin/" in parsed.admin_paths
    assert "/wp-admin/" in parsed.admin_paths
    assert "/debug/" in parsed.debug_paths
    assert "/private/" in parsed.sensitive_paths
    assert "/internal/" in parsed.sensitive_paths


def test_rules_flag_disclosed_paths() -> None:
    raw = RobotsRawResponse(url="https://example.com/robots.txt", status_code=200, body=ROBOTS_SAMPLE)
    parsed = parser.parse(raw)
    asset = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")

    findings = rules.evaluate_rules(parsed, asset, plugin_id="robots")
    rule_ids = {finding.rule_id for finding in findings}

    assert "ROBOTS_ADMIN_PATH_DISCLOSED" in rule_ids
    assert "ROBOTS_DEBUG_PATH_DISCLOSED" in rule_ids
    assert "ROBOTS_SENSITIVE_PATH_DISCLOSED" in rule_ids


def test_missing_robots_produces_no_findings() -> None:
    raw = RobotsRawResponse(url="https://example.com/robots.txt", status_code=404, body="")
    parsed = parser.parse(raw)
    asset = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")

    assert parsed.present is False
    assert rules.evaluate_rules(parsed, asset, plugin_id="robots") == []


def test_build_metadata_lists_parsed_directives() -> None:
    raw = RobotsRawResponse(url="https://example.com/robots.txt", status_code=200, body=ROBOTS_SAMPLE)
    parsed = parser.parse(raw)
    metadata = RobotsPlugin().build_metadata(parsed)

    assert metadata["present"] is True
    assert metadata["disallowed_count"] == 5
    assert metadata["allowed_count"] == 1
    assert metadata["sitemap_count"] == 2
    assert "/admin/" in metadata["admin_paths"]
    assert metadata["sitemaps"][0].endswith("sitemap.xml")
