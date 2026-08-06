from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.rules import (
    evaluate_rules,
    rule_missing_csp,
    rule_missing_hsts,
    rule_no_https_redirect,
    rule_server_header_exposed,
    rule_trace_enabled,
    rule_weak_cookies,
)
from app.plugins.http_headers.schemas import HttpHeadersParsedData, ParsedCookie, SecurityHeaders, HttpTiming


def _parsed(**kwargs) -> HttpHeadersParsedData:
    defaults = {
        "url": "https://example.com",
        "final_url": "https://example.com/",
        "status_code": 200,
        "headers": {},
        "cookies": [],
        "redirects": [],
        "security_headers": SecurityHeaders(),
        "timing": HttpTiming(total_ms=100.0),
        "body_length": 0,
        "is_https": True,
        "http_redirects_to_https": True,
        "trace_enabled": False,
        "weak_cookies": [],
    }
    defaults.update(kwargs)
    return HttpHeadersParsedData(**defaults)


ASSET = ScanTarget(asset_id="1", identifier="example.com", asset_type="website")


def test_rule_missing_csp() -> None:
    finding = rule_missing_csp(_parsed(), ASSET, "http_headers")
    assert finding is not None
    assert finding.rule_id == "HTTP_NO_CSP"
    assert finding.severity.value == "high"


def test_rule_missing_hsts_only_on_https() -> None:
    assert rule_missing_hsts(_parsed(is_https=False), ASSET, "http_headers") is None
    finding = rule_missing_hsts(_parsed(is_https=True), ASSET, "http_headers")
    assert finding is not None
    assert finding.rule_id == "HTTP_NO_HSTS"


def test_rule_server_header_exposed() -> None:
    finding = rule_server_header_exposed(_parsed(server="nginx"), ASSET, "http_headers")
    assert finding is not None
    assert finding.rule_id == "HTTP_SERVER_HEADER_EXPOSED"


def test_rule_trace_enabled() -> None:
    finding = rule_trace_enabled(_parsed(trace_enabled=True), ASSET, "http_headers")
    assert finding is not None
    assert finding.rule_id == "HTTP_TRACE_ENABLED"


def test_rule_no_https_redirect() -> None:
    finding = rule_no_https_redirect(_parsed(http_redirects_to_https=False), ASSET, "http_headers")
    assert finding is not None
    assert finding.rule_id == "HTTP_NO_HTTPS_REDIRECT"


def test_rule_weak_cookies() -> None:
    cookie = ParsedCookie(name="sessionid", secure=False, httponly=False, is_session_like=True)
    finding = rule_weak_cookies(_parsed(weak_cookies=[cookie]), ASSET, "http_headers")
    assert finding is not None
    assert finding.rule_id == "HTTP_WEAK_COOKIE"


def test_evaluate_rules_runs_all_independent_rules() -> None:
    parsed = _parsed(server="nginx")
    findings = evaluate_rules(parsed, ASSET, plugin_id="http_headers")
    rule_ids = {finding.rule_id for finding in findings}
    assert "HTTP_NO_CSP" in rule_ids
    assert "HTTP_NO_HSTS" in rule_ids
    assert "HTTP_NO_REFERRER_POLICY" in rule_ids
    assert "HTTP_NO_X_FRAME_OPTIONS" in rule_ids
    assert "HTTP_NO_X_CONTENT_TYPE_OPTIONS" in rule_ids
    assert "HTTP_SERVER_HEADER_EXPOSED" in rule_ids
    assert "HTTP_MISSING_SECURITY_TXT" in rule_ids
