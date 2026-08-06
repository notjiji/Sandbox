from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.rules import evaluate_rules
from app.plugins.dns.schemas import DnsParsedData


def test_evaluate_rules_flags_missing_spf() -> None:
    parsed = DnsParsedData(domain="example.com", a_records=[], txt_records=[], has_spf=False)
    asset = ScanTarget(asset_id="1", identifier="example.com", asset_type="domain")
    findings = evaluate_rules(parsed, asset, plugin_id="dns")
    assert len(findings) == 1
    assert findings[0].rule_id == "DNS_MISSING_SPF"
