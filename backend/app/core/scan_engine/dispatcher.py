"""Routes scan work to the correct plugin(s) via the plugin registry."""

from app.core.logging import get_logger
from app.plugins.base import ScanResult, ScanTarget
from app.plugins.exceptions import PluginNotFoundError
from app.plugins.manager import manager

logger = get_logger("sandbox.scan_engine.dispatcher")


class ScanDispatcher:
    def dispatch(self, *, plugin_name: str, target: ScanTarget) -> ScanResult:
        try:
            plugin = manager.get_plugin(plugin_name)
            return plugin.scan(target)
        except PluginNotFoundError as exc:
            logger.warning("plugin not found", extra={"plugin": plugin_name})
            return ScanResult(success=False, metadata={"error": str(exc)})
        except Exception as exc:
            logger.exception(
                "plugin execution raised",
                extra={"plugin": plugin_name, "asset_id": target.asset_id},
            )
            return ScanResult(success=False, metadata={"error": str(exc)})
