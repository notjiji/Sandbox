"""TLS cipher rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.tls.schemas import TlsParsedData


def evaluate_rules(parsed: TlsParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules("tls", parsed, asset)
