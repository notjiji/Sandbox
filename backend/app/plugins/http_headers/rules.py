"""HTTP header rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.http_headers.schemas import HttpHeadersParsedData


def evaluate_rules(parsed: HttpHeadersParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules(plugin_id, parsed, asset)
