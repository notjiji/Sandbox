from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.rules import evaluate_rules
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


def test_missing_csp_finding() -> None:
    findings = evaluate_rules(_parsed(), ASSET, plugin_id="http_headers")
    csp = next(f for f in findings if f.rule_id == "HTTP_NO_CSP")
    assert csp.severity is None
    assert "Content-Security-Policy" in (csp.evidence or "")


def test_missing_hsts_only_on_https() -> None:
    assert "HTTP_NO_HSTS" not in {f.rule_id for f in evaluate_rules(_parsed(is_https=False), ASSET, plugin_id="http_headers")}
    findings = evaluate_rules(_parsed(is_https=True), ASSET, plugin_id="http_headers")
    assert "HTTP_NO_HSTS" in {f.rule_id for f in findings}


def test_server_header_exposed() -> None:
    findings = evaluate_rules(_parsed(server="nginx"), ASSET, plugin_id="http_headers")
    assert "HTTP_SERVER_HEADER_EXPOSED" in {f.rule_id for f in findings}


def test_trace_enabled() -> None:
    findings = evaluate_rules(_parsed(trace_enabled=True), ASSET, plugin_id="http_headers")
    assert "HTTP_TRACE_ENABLED" in {f.rule_id for f in findings}


def test_no_https_redirect() -> None:
    findings = evaluate_rules(_parsed(http_redirects_to_https=False), ASSET, plugin_id="http_headers")
    assert "HTTP_NO_HTTPS_REDIRECT" in {f.rule_id for f in findings}


def test_weak_cookies() -> None:
    cookie = ParsedCookie(name="sessionid", secure=False, httponly=False, is_session_like=True)
    findings = evaluate_rules(_parsed(weak_cookies=[cookie]), ASSET, plugin_id="http_headers")
    assert "HTTP_WEAK_COOKIE" in {f.rule_id for f in findings}


def test_evaluate_rules_runs_declarative_rules() -> None:
    findings = evaluate_rules(_parsed(server="nginx"), ASSET, plugin_id="http_headers")
    rule_ids = {finding.rule_id for finding in findings}
    assert "HTTP_NO_CSP" in rule_ids
    assert "HTTP_NO_HSTS" in rule_ids
    assert "HTTP_NO_REFERRER_POLICY" in rule_ids
    assert "HTTP_NO_X_FRAME_OPTIONS" in rule_ids
    assert "HTTP_NO_X_CONTENT_TYPE_OPTIONS" in rule_ids
    assert "HTTP_SERVER_HEADER_EXPOSED" in rule_ids
