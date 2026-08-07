"""Robots.txt rules — evaluated by the declarative rule engine."""

from app.core.rule_engine.engine import evaluate_plugin_rules
from app.plugins.base.plugin import ScanTarget
from app.plugins.robots.schemas import RobotsParsedData


def evaluate_rules(parsed: RobotsParsedData, asset: ScanTarget, *, plugin_id: str):
    return evaluate_plugin_rules(plugin_id, parsed, asset)
