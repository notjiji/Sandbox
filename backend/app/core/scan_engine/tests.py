"""Scan engine unit tests."""


def test_resolve_scan_status_completed_when_any_plugin_succeeds() -> None:
    from app.core.scan_engine.result_combiner import resolve_scan_status
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base import ScanTarget
    from app.scans.enums import PluginRunStatus, ScanStatus

    target = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")
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
            normalized_findings=[{"title": "ok", "severity": "info"}],
        ),
    ]

    assert resolve_scan_status(records) == ScanStatus.COMPLETED


def test_resolve_scan_status_failed_when_all_plugins_fail() -> None:
    from app.core.scan_engine.result_combiner import resolve_scan_status
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base import ScanTarget
    from app.scans.enums import PluginRunStatus, ScanStatus

    target = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")
    records = [
        PluginExecutionRecord(
            plugin_name="dns",
            target=target,
            status=PluginRunStatus.FAILED,
        ),
        PluginExecutionRecord(
            plugin_name="ssl",
            target=target,
            status=PluginRunStatus.SKIPPED,
            error_message="disabled",
        ),
    ]

    assert resolve_scan_status(records) == ScanStatus.FAILED


def test_combine_normalized_findings() -> None:
    from app.core.scan_engine.result_combiner import combine_normalized_findings
    from app.core.scan_engine.types import PluginExecutionRecord
    from app.plugins.base import ScanTarget
    from app.scans.enums import PluginRunStatus

    target = ScanTarget(asset_id="00000000-0000-4000-8000-000000000001", identifier="example.com", asset_type="website")
    records = [
        PluginExecutionRecord(
            plugin_name="dns",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[{"title": "a", "severity": "info"}],
        ),
        PluginExecutionRecord(
            plugin_name="ssl",
            target=target,
            status=PluginRunStatus.COMPLETED,
            normalized_findings=[
                {"title": "b", "severity": "low"},
                {"title": "c", "severity": "medium"},
            ],
        ),
    ]

    combined = combine_normalized_findings(records)
    assert len(combined) == 3
    assert combined[0]["title"] == "a"
    assert combined[-1]["title"] == "c"


def test_registry_returns_enabled_plugins_for_scan_type() -> None:
    from app.core.scan_engine.plugin_loader import PluginLoader
    from app.plugins.registry import registry
    from app.scans.enums import ScanType

    registry._plugins.clear()
    try:
        selection = PluginLoader().select_for_scan(ScanType.QUICK)
        enabled_names = {plugin.name for plugin in selection.enabled}
        assert enabled_names == {"http_headers", "dns"}

        full_selection = PluginLoader().select_for_scan(ScanType.FULL)
        full_names = {plugin.name for plugin in full_selection.enabled}
        assert full_names == {"dns", "http_headers", "ports", "ssl", "whois"}
    finally:
        registry._plugins.clear()
        PluginLoader().ensure_loaded()


def test_registry_skips_disabled_plugins() -> None:
    from app.core.scan_engine.plugin_loader import PluginLoader
    from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
    from app.plugins.registry import registry
    from app.scans.enums import ScanType

    class DisabledPlugin(ScannerPlugin):
        name = "disabled_test_plugin"
        description = "Disabled test plugin"
        version = "0.0.1"
        supported_assets = ["website"]
        supported_scan_types = [ScanType.FULL.value]
        enabled = False

        async def scan(self, asset: ScanTarget) -> ScanResult:
            return ScanResult(success=True)

    registry.register(DisabledPlugin())
    try:
        selection = PluginLoader().select_for_scan(ScanType.FULL)
        disabled_names = {plugin.name for plugin in selection.disabled}
        assert "disabled_test_plugin" in disabled_names
    finally:
        registry._plugins.pop("disabled_test_plugin", None)


def test_dispatcher_runs_async_plugins() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
    from app.plugins.registry import registry
    from app.scans.enums import ScanType

    class AsyncPlugin(ScannerPlugin):
        name = "async_test_plugin"
        description = "Async test plugin"
        version = "0.0.1"
        supported_assets = ["website"]
        supported_scan_types = [ScanType.FULL.value]

        async def scan(self, asset: ScanTarget) -> ScanResult:
            return ScanResult(success=True, findings=[{"title": "async ok", "severity": "info"}])

    registry.register(AsyncPlugin())
    try:
        result = ScanDispatcher().dispatch(
            plugin=AsyncPlugin(),
            asset=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
        )
        assert result.success is True
        assert result.findings[0]["title"] == "async ok"
    finally:
        registry._plugins.pop("async_test_plugin", None)


def test_dispatcher_catches_plugin_errors() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base import ScanTarget, ScannerPlugin
    from app.scans.enums import ScanType

    class BrokenPlugin(ScannerPlugin):
        name = "broken_test_plugin"
        description = "Broken test plugin"
        version = "0.0.1"
        supported_assets = ["website"]
        supported_scan_types = [ScanType.FULL.value]

        async def scan(self, asset: ScanTarget):
            raise RuntimeError("boom")

    plugin = BrokenPlugin()
    result = ScanDispatcher().dispatch(
        plugin=plugin,
        asset=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
    )
    assert result.success is False
    assert "boom" in result.metadata.get("error", "")


def test_plugin_supports_asset_filtering() -> None:
    from app.plugins.ssl.plugin import SslPlugin

    plugin = SslPlugin()
    assert plugin.supports_asset("website") is True
    assert plugin.supports_asset("public_ip") is False
