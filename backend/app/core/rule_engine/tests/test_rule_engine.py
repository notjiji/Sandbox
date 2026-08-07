"""Rule engine unit tests."""

from app.core.rule_engine.conditions import evaluate_condition, matches
from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.schemas import HttpHeadersParsedData, SecurityHeaders, HttpTiming
from app.plugins.robots.schemas import RobotsRawResponse
from app.plugins.robots import parser as robots_parser
from app.plugins.security_txt.schemas import SecurityTxtRawResponse
from app.plugins.security_txt import parser as security_txt_parser


ASSET = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")


def test_header_missing_shorthand() -> None:
    context = {"has_csp": False}
    assert matches({"header_missing": "Content-Security-Policy"}, context) is True
    assert matches({"header_missing": "Content-Security-Policy"}, {"has_csp": True}) is False


def test_and_condition() -> None:
    context = {"present": True, "admin_paths": ["/admin/"]}
    condition = {"op": "and", "conditions": [{"path_truthy": "present"}, {"path_nonempty": "admin_paths"}]}
    assert evaluate_condition(condition, context) is True


def test_http_missing_csp_rule() -> None:
    parsed = HttpHeadersParsedData(
        url="https://example.com",
        final_url="https://example.com/",
        status_code=200,
        headers={},
        cookies=[],
        redirects=[],
        security_headers=SecurityHeaders(),
        timing=HttpTiming(total_ms=100.0),
        body_length=0,
        is_https=True,
        weak_cookies=[],
    )
    findings = evaluate_plugin_rules("http_headers", parsed, ASSET)
    rule_ids = {finding.rule_id for finding in findings}
    assert "HTTP_NO_CSP" in rule_ids


def test_robots_declarative_rules() -> None:
    raw = RobotsRawResponse(
        url="https://example.com/robots.txt",
        status_code=200,
        body="User-agent: *\nDisallow: /admin/\nDisallow: /debug/\n",
    )
    parsed = robots_parser.parse(raw)
    findings = evaluate_plugin_rules("robots", parsed, ASSET)
    rule_ids = {finding.rule_id for finding in findings}
    assert "ROBOTS_ADMIN_PATH_DISCLOSED" in rule_ids
    assert "ROBOTS_DEBUG_PATH_DISCLOSED" in rule_ids


def test_security_txt_declarative_rules() -> None:
    raw = SecurityTxtRawResponse(url="https://example.com/.well-known/security.txt", status_code=404, body="")
    parsed = security_txt_parser.parse(raw)
    findings = evaluate_plugin_rules("security_txt", parsed, ASSET)
    assert any(finding.rule_id == "SECURITY_TXT_MISSING" for finding in findings)
