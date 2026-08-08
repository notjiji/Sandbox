"""Legacy plugin id — delegates to the TLS scanner implementation."""

from app.plugins.base.config import PluginConfig
from app.plugins.base.plugin import ScanTarget
from app.plugins.tls.plugin import TlsPlugin
from app.core.rule_engine.engine import evaluate_plugin_rules


class SslPlugin(TlsPlugin):
    id = "ssl"
    name = "TLS Scanner"
    version = "4.0.0"
    default_config = PluginConfig(enabled=True, timeout=45.0, retries=2, parallel=False, version="4.0.0")

    def evaluate_rules(self, parsed, asset: ScanTarget):
        return evaluate_plugin_rules(self.id, parsed, asset)
