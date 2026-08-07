"""Routes scan work to scanner plugins."""

import asyncio
import inspect
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.plugins.base.contracts import ScanOptions, ScanResult, ScanResultStatus
from app.plugins.base.exceptions import PluginNotFoundError
from app.plugins.base.plugin import ScanTarget, ScannerPlugin

logger = get_logger("sandbox.scan_engine.dispatcher")


class ScanDispatcher:
    async def dispatch_async(
        self,
        *,
        plugin: ScannerPlugin,
        asset: ScanTarget,
        options: ScanOptions | None = None,
    ) -> ScanResult:
        started_at = datetime.now(UTC)
        scan_options = options or plugin.default_options()
        try:
            if not plugin.supports_asset(asset.asset_type):
                message = f"Plugin does not support asset type: {asset.asset_type}"
                return ScanResult.failure(
                    plugin=plugin.id,
                    version=plugin.version,
                    started_at=started_at,
                    error=message,
                )

            result = plugin.run(asset, scan_options)
            if inspect.isawaitable(result):
                output = await result
            else:
                output = result

            validated = ScanResult.model_validate(output.model_dump())
            if validated.plugin != plugin.id:
                validated = validated.model_copy(update={"plugin": plugin.id})
            return validated
        except PluginNotFoundError as exc:
            logger.warning("plugin not found", extra={"plugin": plugin.id})
            return ScanResult.failure(
                plugin=plugin.id,
                version=plugin.version,
                started_at=started_at,
                error=str(exc),
            )
        except Exception as exc:
            logger.exception(
                "plugin execution raised",
                extra={"plugin": plugin.id, "asset_id": asset.asset_id},
            )
            return ScanResult.failure(
                plugin=plugin.id,
                version=plugin.version,
                started_at=started_at,
                error=str(exc),
            )

    async def dispatch_parallel(
        self,
        jobs: list[tuple[ScannerPlugin, ScanTarget]],
    ) -> list[ScanResult]:
        """Run multiple plugin scans concurrently."""
        if not jobs:
            return []
        return list(await asyncio.gather(*(self.dispatch_async(plugin=plugin, asset=target) for plugin, target in jobs)))

    def dispatch(
        self,
        *,
        plugin: ScannerPlugin,
        asset: ScanTarget,
        options: ScanOptions | None = None,
    ) -> ScanResult:
        return asyncio.run(self.dispatch_async(plugin=plugin, asset=asset, options=options))

    @staticmethod
    def is_success(output: ScanResult) -> bool:
        return output.status == ScanResultStatus.SUCCESS
