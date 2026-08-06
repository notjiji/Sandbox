from app.plugins.base.plugin import ScanTarget
from app.plugins.dns.rules import evaluate_rules, rule_missing_spf, rule_weak_dmarc
from app.plugins.dns.schemas import DnsParsedData


ASSET = ScanTarget(asset_id="1", identifier="example.com", asset_type="domain")


def test_evaluate_rules_flags_missing_spf() -> None:
    parsed = DnsParsedData(domain="example.com")
    findings = evaluate_rules(parsed, ASSET, plugin_id="dns")
    assert any(f.rule_id == "DNS_MISSING_SPF" for f in findings)


def test_rule_weak_dmarc() -> None:
    parsed = DnsParsedData(domain="example.com", dmarc_record="v=DMARC1; p=none", dmarc_is_weak=True)
    finding = rule_weak_dmarc(parsed, ASSET, "dns")
    assert finding is not None
    assert finding.rule_id == "DNS_WEAK_DMARC"
