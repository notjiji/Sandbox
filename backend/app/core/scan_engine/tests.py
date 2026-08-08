"""Scan engine unit tests."""

from datetime import UTC, datetime

ASSET_ID = "00000000-0000-4000-8000-000000000001"


def test_resolve_scan_status_completed_when_any_plugin_succeeds() -> None:
    from app.core.scan_engine.result_combiner import resolve_scan_status
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base.output import PluginFinding, PluginFindingStatus
    from app.plugins.base.plugin import ScanTarget
    from app.scans.enums import PluginRunStatus, ScanStatus

    target = ScanTarget(asset_id=ASSET_ID, identifier="example.com", asset_type="website")
    finding = PluginFinding(
        plugin="ssl",
        rule_id="SSL_TLS10_ENABLED",
        asset_id=ASSET_ID,
        title="TLS 1.0 Enabled",
        status=PluginFindingStatus.FAILED,
    )
    records = [
        PluginExecutionRecord(
            plugin_name="dns",
            target=target,
            status=PluginRunStatus.FAILED,
            error_message="timeout",
        ),
        PluginExecutionRecord(
            plugin_name="ssl",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[finding],
        ),
    ]

    assert resolve_scan_status(records) == ScanStatus.COMPLETED


def test_combine_normalized_findings() -> None:
    from app.core.scan_engine.result_combiner import combine_normalized_findings
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base.output import PluginFinding, PluginFindingStatus
    from app.plugins.base.plugin import ScanTarget
    from app.scans.enums import PluginRunStatus

    target = ScanTarget(asset_id=ASSET_ID, identifier="example.com", asset_type="website")
    records = [
        PluginExecutionRecord(
            plugin_name="dns",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[
                PluginFinding(
                    plugin="dns",
                    rule_id="DNS_MISSING_SPF",
                    asset_id=ASSET_ID,
                    title="Missing SPF record",
                    status=PluginFindingStatus.FAILED,
                )
            ],
        ),
        PluginExecutionRecord(
            plugin_name="ssl",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[
                PluginFinding(
                    plugin="ssl",
                    rule_id="SSL_TLS10_ENABLED",
                    asset_id=ASSET_ID,
                    title="TLS 1.0 Enabled",
                    status=PluginFindingStatus.FAILED,
                ),
                PluginFinding(
                    plugin="ssl",
                    rule_id="SSL_EXPIRED",
                    asset_id=ASSET_ID,
                    title="Certificate expired",
                    status=PluginFindingStatus.FAILED,
                ),
            ],
        ),
    ]

    combined = combine_normalized_findings(records)
    assert len(combined) == 3


def test_scan_result_schema() -> None:
    from app.plugins.base.contracts import ScanResultStatus
    from app.plugins.base.output import PluginOutput, report_finding

    started_at = datetime.now(UTC)
    finished_at = datetime.now(UTC)
    output = PluginOutput(
        plugin="ssl",
        version="1.0",
        started_at=started_at,
        finished_at=finished_at,
        status=ScanResultStatus.SUCCESS,
        findings=[
            report_finding(
                plugin="ssl",
                rule_id="SSL_EXPIRED",
                asset_id=ASSET_ID,
                title="Certificate expired",
                evidence="cert expired",
            )
        ],
        metadata={"issuer": "Let's Encrypt"},
    )
    payload = output.model_dump()
    assert payload["plugin"] == "ssl"
    assert payload["version"] == "1.0"
    assert payload["status"] == "success"
    assert payload["duration_ms"] == 0
    assert payload["findings"][0]["rule_id"] == "SSL_EXPIRED"
    assert "score" not in payload["findings"][0]


def test_scan_result_timeout_shape() -> None:
    from app.plugins.base.contracts import ScanResult, ScanResultStatus

    started_at = datetime.now(UTC)
    output = ScanResult.timeout(
        plugin="ssl",
        version="3.1.0",
        started_at=started_at,
        error="TLS handshake timed out",
    )
    payload = output.model_dump()
    assert payload["plugin"] == "ssl"
    assert payload["status"] == ScanResultStatus.TIMEOUT.value
    assert payload["error"] == "TLS handshake timed out"
    assert payload["findings"] == []
    assert payload["duration_ms"] >= 0


def test_profile_resolves_quick_scan_plugins() -> None:
    from types import SimpleNamespace

    from app.plugins.base.loader import plugin_loader
    from app.plugins.base.registry import registry
    from app.scans.enums import ScanType

    registry._plugins.clear()
    try:
        scan = SimpleNamespace(scan_type=ScanType.QUICK, selected_plugins=None)
        selection = plugin_loader.select_for_scan(scan)
        enabled_ids = {plugin.id for plugin in selection.enabled}
        assert enabled_ids == {"http_headers", "tls", "dns", "cookies"}
    finally:
        registry._plugins.clear()
        plugin_loader.discover()


def test_profile_resolves_custom_scan_plugins() -> None:
    from types import SimpleNamespace

    from app.plugins.base.loader import plugin_loader
    from app.plugins.base.registry import registry
    from app.scans.enums import ScanType

    registry._plugins.clear()
    try:
        scan = SimpleNamespace(scan_type=ScanType.CUSTOM, selected_plugins=["dns", "whois"])
        selection = plugin_loader.select_for_scan(scan)
        enabled_ids = {plugin.id for plugin in selection.enabled}
        assert enabled_ids == {"dns", "whois"}
    finally:
        registry._plugins.clear()
        plugin_loader.discover()


def test_plugin_loader_discovers_all_builtin_plugins() -> None:
    from app.plugins.base.loader import BUILTIN_PLUGIN_CLASSES, plugin_loader
    from app.plugins.base.registry import registry

    registry._plugins.clear()
    try:
        names = plugin_loader.discover()
        assert len(names) == len(BUILTIN_PLUGIN_CLASSES)
        assert "robots" in names
        assert "tls" in names
        assert "cookies" in names
        assert "malware" in names
    finally:
        registry._plugins.clear()
        plugin_loader.discover()


def test_dispatcher_runs_async_plugins() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base.config import PluginConfig
    from app.plugins.base.contracts import ScanOptions, ScanResult
    from app.plugins.base.plugin import ScanTarget, ScannerPlugin
    from app.scans.enums import ScanType

    class AsyncPlugin(ScannerPlugin):
        id = "async_test_plugin"
        name = "Async Test Plugin"
        version = "0.0.1"
        supported_asset_types = ["website"]
        supported_scan_types = [ScanType.FULL.value]
        default_config = PluginConfig(version="0.0.1")

        async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
            started_at = datetime.now(UTC)
            return ScanResult.success(
                plugin=self.id,
                version=self.version,
                started_at=started_at,
                findings=[],
                metadata={},
            )

    result = ScanDispatcher().dispatch(
        plugin=AsyncPlugin(),
        asset=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
    )
    assert result.status.value == "success"
    assert result.duration >= 0


def test_dispatcher_catches_plugin_errors() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base.config import PluginConfig
    from app.plugins.base.contracts import ScanOptions
    from app.plugins.base.plugin import ScanTarget, ScannerPlugin
    from app.scans.enums import ScanType

    class BrokenPlugin(ScannerPlugin):
        id = "broken_test_plugin"
        name = "Broken Test Plugin"
        version = "0.0.1"
        supported_asset_types = ["website"]
        supported_scan_types = [ScanType.FULL.value]
        default_config = PluginConfig(version="0.0.1")

        async def run(self, asset: ScanTarget, options: ScanOptions):
            raise RuntimeError("boom")

    result = ScanDispatcher().dispatch(
        plugin=BrokenPlugin(),
        asset=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
    )
    assert result.status.value == "failed"
    assert "boom" in (result.error or "")


def test_dispatcher_runs_plugins_in_parallel() -> None:
    import asyncio
    import time

    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base.config import PluginConfig
    from app.plugins.base.contracts import ScanOptions, ScanResult
    from app.plugins.base.plugin import ScanTarget, ScannerPlugin
    from app.scans.enums import ScanType

    class SlowPlugin(ScannerPlugin):
        def __init__(self, plugin_id: str) -> None:
            self.id = plugin_id
            self.name = plugin_id
            self.version = "0.0.1"
            self.supported_asset_types = ["website"]
            self.supported_scan_types = [ScanType.FULL.value]
            self.default_config = PluginConfig(version="0.0.1")

        async def run(self, asset: ScanTarget, options: ScanOptions) -> ScanResult:
            await asyncio.sleep(0.05)
            started_at = datetime.now(UTC)
            return ScanResult.success(
                plugin=self.id,
                version=self.version,
                started_at=started_at,
                findings=[],
                metadata={},
            )

    target = ScanTarget(asset_id="1", identifier="vinca.family", asset_type="website")
    jobs = [(SlowPlugin("http_headers"), target), (SlowPlugin("ssl"), target), (SlowPlugin("dns"), target)]

    started = time.perf_counter()
    results = asyncio.run(ScanDispatcher().dispatch_parallel(jobs))
    elapsed = time.perf_counter() - started

    assert len(results) == 3
    assert all(result.status.value == "success" for result in results)
    assert elapsed < 0.12


def test_dispatcher_maps_wait_for_timeout() -> None:
    import asyncio

    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base.config import PluginConfig
    from app.plugins.base.contracts import ScanOptions, ScanResultStatus
    from app.plugins.base.plugin import ScanTarget, ScannerPlugin
    from app.scans.enums import ScanType

    class HangingPlugin(ScannerPlugin):
        id = "ssl"
        name = "SSL Scanner"
        version = "3.1.0"
        supported_asset_types = ["website"]
        supported_scan_types = [ScanType.FULL.value]
        default_config = PluginConfig(timeout=0.05, version="3.1.0")

        async def run(self, asset: ScanTarget, options: ScanOptions):
            await asyncio.sleep(1)
            raise AssertionError("should have timed out")

    result = ScanDispatcher().dispatch(
        plugin=HangingPlugin(),
        asset=ScanTarget(asset_id="1", identifier="vinca.family", asset_type="website"),
    )
    assert result.status == ScanResultStatus.TIMEOUT
    assert result.error is not None
    assert "timed out" in result.error.lower()
    assert result.duration_ms >= 0


def test_orchestrator_continues_when_one_plugin_fails() -> None:
    from app.core.scan_engine.orchestrator import ScanOrchestrator
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base.contracts import ScanResult, ScanResultStatus
    from app.plugins.base.plugin import ScanTarget
    from app.scans.enums import PluginRunStatus

    target = ScanTarget(asset_id=ASSET_ID, identifier="vinca.family", asset_type="website")
    started_at = datetime.now(UTC)
    records = [
        PluginExecutionRecord(
            plugin_name="ssl",
            target=target,
            status=PluginRunStatus.FAILED,
            output=ScanResult.timeout(
                plugin="ssl",
                version="3.1.0",
                started_at=started_at,
                error="TLS handshake timed out",
            ),
            error_message="TLS handshake timed out",
        ),
        PluginExecutionRecord(
            plugin_name="dns",
            target=target,
            status=PluginRunStatus.COMPLETED,
            output=ScanResult.success(
                plugin="dns",
                version="3.1.0",
                started_at=started_at,
                findings=[],
            ),
        ),
    ]

    from app.core.scan_engine.result_combiner import resolve_scan_status

    assert resolve_scan_status(records).value == "completed"
    assert ScanOrchestrator()._combine_results(records).completed_plugins == 1
    assert ScanOrchestrator()._combine_results(records).failed_plugins == 1


def test_plugin_config_exposed() -> None:
    from app.plugins.ssl.plugin import SslPlugin

    plugin = SslPlugin()
    assert plugin.config.enabled is True
    assert plugin.config.timeout == 45.0
    assert plugin.config.retries == 2
    assert plugin.config.version == "4.0.0"
