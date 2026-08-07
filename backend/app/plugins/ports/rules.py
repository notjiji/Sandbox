"""Port exposure rules — evaluated by the declarative rule engine."""

from collections.abc import Callable

from app.core.rule_engine.catalog import get_plugin_rules
from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.ports.schemas import PortsParsedData

RuleFn = Callable[[PortsParsedData, ScanTarget, str], object | None]


def _single_rule(finding_code: str) -> RuleFn:
    rules = [rule for rule in get_plugin_rules("ports") if rule.finding_code == finding_code]

    def evaluate(parsed: PortsParsedData, asset: ScanTarget, plugin_id: str):
        findings = evaluate_plugin_rules("ports", parsed, asset, rules=rules)
        return findings[0] if findings else None

    return evaluate


rule_ftp_open = _single_rule("PORT_FTP_OPEN")
rule_telnet_open = _single_rule("PORT_TELNET_OPEN")
rule_rdp_exposed = _single_rule("PORT_RDP_EXPOSED")
rule_mysql_public = _single_rule("PORT_MYSQL_PUBLIC")
rule_redis_public = _single_rule("PORT_REDIS_PUBLIC")
rule_mongodb_public = _single_rule("PORT_MONGODB_PUBLIC")


def evaluate_rules(parsed: PortsParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules("ports", parsed, asset)
