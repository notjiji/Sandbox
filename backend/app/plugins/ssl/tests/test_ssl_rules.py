from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.rules import evaluate_rules
from app.plugins.ssl.schemas import SslParsedData


def test_evaluate_rules_flags_tls10() -> None:
    parsed = SslParsedData(
        protocols=["TLSv1.0", "TLSv1.2"],
        issuer="Let's Encrypt",
        expires="2026-12-01",
        cipher_suites=[],
    )
    asset = ScanTarget(asset_id="asset-1", identifier="example.com", asset_type="website")

    findings = evaluate_rules(parsed, asset, plugin_id="ssl")

    assert len(findings) == 1
    assert findings[0].rule_id == "SSL_TLS10_ENABLED"


def test_evaluate_rules_passes_when_tls10_absent() -> None:
    parsed = SslParsedData(
        protocols=["TLSv1.2", "TLSv1.3"],
        issuer="Let's Encrypt",
        expires="2026-12-01",
        cipher_suites=[],
    )
    asset = ScanTarget(asset_id="asset-1", identifier="example.com", asset_type="website")

    findings = evaluate_rules(parsed, asset, plugin_id="ssl")

    assert findings == []
