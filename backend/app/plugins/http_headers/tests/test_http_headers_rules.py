from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.rules import evaluate_rules
from app.plugins.http_headers.schemas import HttpHeadersParsedData


def test_evaluate_rules_flags_csp_and_hsts() -> None:
    parsed = HttpHeadersParsedData(status_code=200, headers={}, has_csp=False, has_hsts=False)
    asset = ScanTarget(asset_id="1", identifier="example.com", asset_type="website")
    findings = evaluate_rules(parsed, asset, plugin_id="http_headers")
    rule_ids = {finding.rule_id for finding in findings}
    assert rule_ids == {"HTTP_NO_CSP", "HTTP_NO_HSTS"}
