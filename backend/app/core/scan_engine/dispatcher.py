"""Routes scan work to scanner plugins."""

import asyncio
import inspect
from datetime import UTC, datetime

from app.core.logging import get_logger
from app.plugins.base.contracts import ScanOptions, ScanResult, ScanResultStatus
from app.plugins.base.exceptions import PluginNotFoundError
from app.plugins.base.plugin import ScanTarget, ScannerPlugin

logger = get_logger("sandbox.scan_engine.dispatcher")

try:
    import httpx
except ImportError:  # pragma: no cover
    httpx = None


def _is_timeout_error(exc: BaseException) -> bool:
    if isinstance(exc, (TimeoutError, asyncio.TimeoutError)):
        return True
    if httpx is not None and isinstance(exc, httpx.TimeoutException):
        return True
    message = str(exc).lower()
    return "timed out" in message or "timeout" in message


class ScanDispatcher:
    async def _execute_plugin(
        self,
        *,
        plugin: ScannerPlugin,
        asset: ScanTarget,
        scan_options: ScanOptions,
        started_at: datetime,
    ) -> ScanResult:
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

        validated = output if isinstance(output, ScanResult) else ScanResult.model_validate(output)
        if validated.plugin != plugin.id:
            validated = validated.model_copy(update={"plugin": plugin.id})
        return validated

    async def dispatch_async(
        self,
        *,
        plugin: ScannerPlugin,
        asset: ScanTarget,
        options: ScanOptions | None = None,
    ) -> ScanResult:
        started_at = datetime.now(UTC)
        scan_options = options or plugin.default_options()
        timeout_seconds = scan_options.timeout if scan_options.timeout > 0 else None

        try:
            if timeout_seconds is None:
                return await self._execute_plugin(
                    plugin=plugin,
                    asset=asset,
                    scan_options=scan_options,
                    started_at=started_at,
                )
            return await asyncio.wait_for(
                self._execute_plugin(
                    plugin=plugin,
                    asset=asset,
                    scan_options=scan_options,
                    started_at=started_at,
                ),
                timeout=timeout_seconds,
            )
        except PluginNotFoundError as exc:
            logger.warning("plugin not found", extra={"plugin": plugin.id})
            return ScanResult.failure(
                plugin=plugin.id,
                version=plugin.version,
                started_at=started_at,
                error=str(exc),
            )
        except Exception as exc:
            if _is_timeout_error(exc):
                logger.warning(
                    "plugin timed out",
                    extra={"plugin": plugin.id, "asset_id": asset.asset_id, "timeout": timeout_seconds},
                )
                return ScanResult.timeout(
                    plugin=plugin.id,
                    version=plugin.version,
                    started_at=started_at,
                    error=f"{plugin.name} timed out after {timeout_seconds}s",
                )
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
        """Run multiple plugin scans concurrently — failures are isolated per plugin."""
        if not jobs:
            return []
        return list(
            await asyncio.gather(
                *(self.dispatch_async(plugin=plugin, asset=target) for plugin, target in jobs),
                return_exceptions=False,
            )
        )

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
