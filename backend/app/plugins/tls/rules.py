"""TLS rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.ssl.schemas import SslParsedData


def evaluate_rules(parsed: SslParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules(plugin_id, parsed, asset)
