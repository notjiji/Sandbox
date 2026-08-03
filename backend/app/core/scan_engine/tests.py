"""Scan engine unit tests."""


def test_resolve_scan_status_completed_when_any_plugin_succeeds() -> None:
    from app.core.scan_engine.result_combiner import resolve_scan_status
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base import ScanTarget
    from app.plugins.output import PluginFinding, PluginFindingStatus
    from app.scans.enums import PluginRunStatus, ScanStatus

    target = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")
    finding = PluginFinding(plugin="ssl", code="SSL_TLS10_ENABLED", status=PluginFindingStatus.FAILED)
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
    from app.plugins.base import ScanTarget
    from app.plugins.output import PluginFinding, PluginFindingStatus
    from app.scans.enums import PluginRunStatus

    target = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")
    records = [
        PluginExecutionRecord(
            plugin_name="dns",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[
                PluginFinding(plugin="dns", code="DNS_MISSING_SPF", status=PluginFindingStatus.FAILED)
            ],
        ),
        PluginExecutionRecord(
            plugin_name="ssl",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[
                PluginFinding(plugin="ssl", code="SSL_TLS10_ENABLED", status=PluginFindingStatus.FAILED),
                PluginFinding(plugin="ssl", code="SSL_EXPIRED", status=PluginFindingStatus.FAILED),
            ],
        ),
    ]

    combined = combine_normalized_findings(records)
    assert len(combined) == 3


def test_plugin_output_schema() -> None:
    from app.plugins.output import PluginOutput, PluginOutputStatus, report_finding

    output = PluginOutput(
        plugin="ssl",
        status=PluginOutputStatus.COMPLETED,
        duration=1.42,
        findings=[report_finding(plugin="ssl", code="SSL_EXPIRED", evidence="cert expired")],
        metadata={"issuer": "Let's Encrypt"},
    )
    payload = output.model_dump()
    assert payload["plugin"] == "ssl"
    assert payload["findings"][0]["code"] == "SSL_EXPIRED"
    assert "severity" not in payload["findings"][0]


def test_profile_resolves_quick_scan_plugins() -> None:
    from types import SimpleNamespace

    from app.core.scan_engine.plugin_loader import PluginLoader
    from app.plugins.registry import registry
    from app.scans.enums import ScanType

    registry._plugins.clear()
    try:
        scan = SimpleNamespace(scan_type=ScanType.QUICK, selected_plugins=None)
        selection = PluginLoader().select_for_scan(scan)
        enabled_names = {plugin.name for plugin in selection.enabled}
        assert enabled_names == {"http_headers", "ssl", "dns"}
    finally:
        registry._plugins.clear()
        PluginLoader().ensure_loaded()


def test_profile_resolves_custom_scan_plugins() -> None:
    from types import SimpleNamespace

    from app.core.scan_engine.plugin_loader import PluginLoader
    from app.plugins.registry import registry
    from app.scans.enums import ScanType

    registry._plugins.clear()
    try:
        scan = SimpleNamespace(scan_type=ScanType.CUSTOM, selected_plugins=["dns", "whois"])
        selection = PluginLoader().select_for_scan(scan)
        enabled_names = {plugin.name for plugin in selection.enabled}
        assert enabled_names == {"dns", "whois"}
    finally:
        registry._plugins.clear()
        PluginLoader().ensure_loaded()


def test_dispatcher_runs_async_plugins() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base import ScanTarget, ScannerPlugin
    from app.plugins.config import PluginConfig
    from app.plugins.output import PluginOutput
    from app.scans.enums import ScanType

    class AsyncPlugin(ScannerPlugin):
        name = "async_test_plugin"
        description = "Async test plugin"
        supported_assets = ["website"]
        supported_scan_types = [ScanType.FULL.value]
        default_config = PluginConfig(version="0.0.1")

        async def scan(self, asset: ScanTarget) -> PluginOutput:
            return PluginOutput.completed(
                plugin=self.name,
                duration=0.5,
                findings=[],
                metadata={},
            )

    result = ScanDispatcher().dispatch(
        plugin=AsyncPlugin(),
        asset=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
    )
    assert result.status.value == "completed"
    assert result.duration > 0


def test_dispatcher_catches_plugin_errors() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base import ScanTarget, ScannerPlugin
    from app.plugins.config import PluginConfig
    from app.scans.enums import ScanType

    class BrokenPlugin(ScannerPlugin):
        name = "broken_test_plugin"
        description = "Broken test plugin"
        supported_assets = ["website"]
        supported_scan_types = [ScanType.FULL.value]
        default_config = PluginConfig(version="0.0.1")

        async def scan(self, asset: ScanTarget):
            raise RuntimeError("boom")

    result = ScanDispatcher().dispatch(
        plugin=BrokenPlugin(),
        asset=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
    )
    assert result.status.value == "failed"
    assert "boom" in (result.error or "")


def test_plugin_config_exposed() -> None:
    from app.plugins.ssl.plugin import SslPlugin

    plugin = SslPlugin()
    assert plugin.config.enabled is True
    assert plugin.config.timeout == 45.0
    assert plugin.config.retries == 2
    assert plugin.config.version == "0.1.0"
