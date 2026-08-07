"""WHOIS scanner unit tests."""

from datetime import UTC, datetime, timedelta

from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.parser import parse
from app.plugins.whois.rules import evaluate_rules, rule_expired, rule_expiring_soon, rule_privacy_disabled, rule_unknown_registrar
from app.plugins.whois.schemas import WhoisParsedData, WhoisRawResponse
from app.plugins.whois.utils import extract_domain, is_unknown_registrar, privacy_is_enabled

ASSET = ScanTarget(asset_id="1", identifier="example.com", asset_type="domain")


def test_extract_domain() -> None:
    assert extract_domain("https://www.example.com/path") == "example.com"


def test_parse_detects_expiring_and_privacy() -> None:
    expires = datetime.now(UTC) + timedelta(days=10)
    raw = WhoisRawResponse(
        domain="example.com",
        registrar="Example Registrar, Inc.",
        created=datetime(2020, 1, 1, tzinfo=UTC),
        updated=datetime(2024, 1, 1, tzinfo=UTC),
        expires=expires,
        name_servers=["ns1.example.com", "ns2.example.com"],
        registrant="Example Org",
        emails=["admin@example.com"],
        raw_text="Registrar: Example Registrar, Inc.",
    )

    parsed = parse(raw)

    assert parsed.expiring_soon is True
    assert parsed.privacy_disabled is True
    assert parsed.unknown_registrar is False
    assert parsed.name_servers == ["ns1.example.com", "ns2.example.com"]


def test_parse_detects_expired_domain() -> None:
    raw = WhoisRawResponse(
        domain="example.com",
        registrar="Example Registrar, Inc.",
        expires=datetime.now(UTC) - timedelta(days=3),
    )
    parsed = parse(raw)
    assert parsed.is_expired is True
    finding = rule_expired(parsed, ASSET, "whois")
    assert finding is not None
    assert finding.rule_id == "WHOIS_EXPIRED"


def test_privacy_enabled_when_redacted() -> None:
    assert privacy_is_enabled(text="Registrant Email: REDACTED FOR PRIVACY", registrant=None, emails=[]) is True


def test_unknown_registrar() -> None:
    assert is_unknown_registrar(None) is True
    assert is_unknown_registrar("unknown") is True
    parsed = WhoisParsedData(domain="example.com", unknown_registrar=True)
    finding = rule_unknown_registrar(parsed, ASSET, "whois")
    assert finding is not None
    assert finding.rule_id == "WHOIS_UNKNOWN_REGISTRAR"


def test_evaluate_rules_expiring_soon() -> None:
    parsed = WhoisParsedData(domain="example.com", expiring_soon=True, days_until_expiry=14)
    findings = evaluate_rules(parsed, ASSET, plugin_id="whois")
    assert any(f.rule_id == "WHOIS_EXPIRING_SOON" for f in findings)


def test_rule_privacy_disabled() -> None:
    parsed = WhoisParsedData(domain="example.com", privacy_disabled=True)
    finding = rule_privacy_disabled(parsed, ASSET, "whois")
    assert finding is not None
    assert finding.rule_id == "WHOIS_PRIVACY_DISABLED"


def test_rule_expiring_soon_skips_expired() -> None:
    parsed = WhoisParsedData(domain="example.com", is_expired=True, expiring_soon=True, days_until_expiry=-1)
    assert rule_expiring_soon(parsed, ASSET, "whois") is None
