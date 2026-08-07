"""Cloud posture rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.future.cloud.schemas import CloudParsedData


def evaluate_rules(parsed: CloudParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules("cloud", parsed, asset)
