"""Routes scan work to the correct plugin(s) via the plugin registry."""

from app.plugins.base import ScanResult, ScanTarget
from app.plugins.manager import manager


class ScanDispatcher:
    def dispatch(self, *, plugin_name: str, target: ScanTarget) -> ScanResult:
        plugin = manager.get_plugin(plugin_name)
        return plugin.scan(target)
