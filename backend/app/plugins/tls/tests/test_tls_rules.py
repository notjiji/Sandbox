"""Cross-plugin TLS + HTTP hint tests."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.shared.scan_context import scan_context
from app.plugins.ssl.schemas import ParsedCertificate, SslParsedData

ASSET = ScanTarget(asset_id="1", identifier="example.com", asset_type="website")


def _parsed(**kwargs) -> SslParsedData:
    cert = ParsedCertificate(issuer="CN=CA", subject="CN=example.com", common_name="example.com")
    defaults = {
        "host": "example.com",
        "port": 443,
        "protocols": ["TLSv1.2"],
        "protocols_accepted": ["TLSv1.2"],
        "certificate": cert,
        "hostname_matches": True,
        "chain_trusted": True,
    }
    defaults.update(kwargs)
    return SslParsedData(**defaults)


def test_tls_no_hsts_when_transport_hints_missing_hsts() -> None:
    scan_context.begin()
    try:
        scan_context.publish_transport_hints({"has_hsts": False, "is_https": True})
        findings = evaluate_plugin_rules("tls", _parsed(), ASSET)
    finally:
        scan_context.end()
    assert any(finding.rule_id == "TLS_NO_HSTS" for finding in findings)
