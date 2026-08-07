"""WHOIS rules — evaluated by the declarative rule engine."""

from collections.abc import Callable

from app.core.rule_engine.catalog import get_plugin_rules
from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.whois.schemas import WhoisParsedData

RuleFn = Callable[[WhoisParsedData, ScanTarget, str], object | None]


def _single_rule(finding_code: str) -> RuleFn:
    rules = [rule for rule in get_plugin_rules("whois") if rule.finding_code == finding_code]

    def evaluate(parsed: WhoisParsedData, asset: ScanTarget, plugin_id: str):
        findings = evaluate_plugin_rules("whois", parsed, asset, rules=rules)
        return findings[0] if findings else None

    return evaluate


rule_expired = _single_rule("WHOIS_EXPIRED")
rule_expiring_soon = _single_rule("WHOIS_EXPIRING_SOON")
rule_privacy_disabled = _single_rule("WHOIS_PRIVACY_DISABLED")
rule_unknown_registrar = _single_rule("WHOIS_UNKNOWN_REGISTRAR")


def evaluate_rules(parsed: WhoisParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules("whois", parsed, asset)
