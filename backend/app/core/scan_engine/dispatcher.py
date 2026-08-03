"""Routes scan work to scanner plugins via the registry."""

import asyncio
import inspect

from app.core.logging import get_logger
from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
from app.plugins.exceptions import PluginNotFoundError

logger = get_logger("sandbox.scan_engine.dispatcher")


class ScanDispatcher:
    def dispatch(self, *, plugin: ScannerPlugin, asset: ScanTarget) -> ScanResult:
        try:
            if not plugin.supports_asset(asset.asset_type):
                return ScanResult(
                    success=False,
                    metadata={"error": f"Plugin does not support asset type: {asset.asset_type}"},
                )
            result = plugin.scan(asset)
            if inspect.isawaitable(result):
                return asyncio.run(result)
            return result
        except PluginNotFoundError as exc:
            logger.warning("plugin not found", extra={"plugin": plugin.name})
            return ScanResult(success=False, metadata={"error": str(exc)})
        except Exception as exc:
            logger.exception(
                "plugin execution raised",
                extra={"plugin": plugin.name, "asset_id": asset.asset_id},
            )
            return ScanResult(success=False, metadata={"error": str(exc)})
