"""Cookie rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.cookies.schemas import CookiesParsedData


def evaluate_rules(parsed: CookiesParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules(plugin_id, parsed, asset)
