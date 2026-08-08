"""Cookie scanner unit tests."""

from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies.parser import parse
from app.plugins.cookies.rules import evaluate_rules
from app.plugins.cookies.schemas import CookiesRawResponse

ASSET = ScanTarget(asset_id="1", identifier="https://example.com", asset_type="website")


def test_parser_detects_missing_secure_and_httponly() -> None:
    raw = CookiesRawResponse(
        url="https://example.com",
        final_url="https://example.com/",
        is_https=True,
        set_cookie_headers=[
            "session=abc123; Path=/",
            "tracking=xyz; Path=/; Secure; HttpOnly; SameSite=Lax",
        ],
    )
    parsed = parse(raw)
    assert len(parsed.cookies) == 2
    assert parsed.cookies[0].name == "session"
    assert parsed.cookies[0].is_sensitive is True
    assert len(parsed.cookies_missing_secure) == 1
    assert len(parsed.cookies_missing_httponly) == 1
    assert len(parsed.cookies_missing_samesite) == 1


def test_rules_flag_insecure_session_cookie() -> None:
    raw = CookiesRawResponse(
        url="https://example.com",
        final_url="https://example.com/",
        is_https=True,
        set_cookie_headers=["session=abc123; Path=/"],
    )
    parsed = parse(raw)
    findings = evaluate_rules(parsed, ASSET, plugin_id="cookies")
    codes = {finding.rule_id for finding in findings}
    assert "COOKIE_MISSING_SECURE" in codes
    assert "COOKIE_MISSING_HTTPONLY" in codes
    assert "COOKIE_MISSING_SAMESITE" in codes
    assert "COOKIE_SENSITIVE_INSECURE" in codes


def test_parser_detects_duplicate_and_oversized_cookies() -> None:
    oversized_value = "x" * 5000
    raw = CookiesRawResponse(
        url="https://example.com",
        final_url="https://example.com/",
        is_https=True,
        set_cookie_headers=[
            f"token=a; Path=/; Secure; HttpOnly; SameSite=Strict",
            f"token=b; Path=/admin; Secure; HttpOnly; SameSite=Strict",
            f"big={oversized_value}; Path=/; Secure; HttpOnly; SameSite=Lax",
        ],
    )
    parsed = parse(raw)
    assert parsed.duplicate_names == ["token"]
    assert len(parsed.cookies_oversized) == 1


def test_parser_flags_weak_names_as_metadata_only() -> None:
    raw = CookiesRawResponse(
        url="https://example.com",
        final_url="https://example.com/",
        is_https=True,
        set_cookie_headers=["admin=1; Secure; HttpOnly; SameSite=Strict"],
    )
    parsed = parse(raw)
    assert parsed.weak_name_cookies == ["admin"]
    findings = evaluate_rules(parsed, ASSET, plugin_id="cookies")
    assert not any("WEAK_NAME" in finding.rule_id for finding in findings)
