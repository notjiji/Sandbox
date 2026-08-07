"""security.txt rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.security_txt.schemas import SecurityTxtParsedData


def evaluate_rules(parsed: SecurityTxtParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules(plugin_id, parsed, asset)
