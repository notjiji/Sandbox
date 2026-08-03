"""Routes scan work to scanner plugins via the registry."""

import asyncio
import inspect
import time

from app.core.logging import get_logger
from app.plugins.base import ScanTarget, ScannerPlugin
from app.plugins.exceptions import PluginNotFoundError
from app.plugins.output import PluginOutput, PluginOutputStatus

logger = get_logger("sandbox.scan_engine.dispatcher")


class ScanDispatcher:
    def dispatch(self, *, plugin: ScannerPlugin, asset: ScanTarget) -> PluginOutput:
        started = time.perf_counter()
        try:
            if not plugin.supports_asset(asset.asset_type):
                duration = time.perf_counter() - started
                message = f"Plugin does not support asset type: {asset.asset_type}"
                return PluginOutput.failed(plugin=plugin.name, duration=duration, error=message)

            result = plugin.scan(asset)
            if inspect.isawaitable(result):
                output = asyncio.run(result)
            else:
                output = result

            duration = time.perf_counter() - started
            if output.duration <= 0:
                output = output.model_copy(update={"duration": round(duration, 3)})
            return PluginOutput.model_validate(output.model_dump())
        except PluginNotFoundError as exc:
            duration = time.perf_counter() - started
            logger.warning("plugin not found", extra={"plugin": plugin.name})
            return PluginOutput.failed(plugin=plugin.name, duration=duration, error=str(exc))
        except Exception as exc:
            duration = time.perf_counter() - started
            logger.exception(
                "plugin execution raised",
                extra={"plugin": plugin.name, "asset_id": asset.asset_id},
            )
            return PluginOutput.failed(plugin=plugin.name, duration=duration, error=str(exc))

    @staticmethod
    def is_success(output: PluginOutput) -> bool:
        return output.status == PluginOutputStatus.COMPLETED
