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


def test_plugin_loader_skips_disabled_plugins() -> None:
    from app.core.scan_engine.plugin_loader import PluginLoader
    from app.plugins.base import ScanResult, ScanTarget, ScannerPlugin
    from app.plugins.registry import registry

    class DisabledPlugin(ScannerPlugin):
        name = "disabled_test_plugin"
        version = "0.0.1"
        enabled = False

        def scan(self, target: ScanTarget) -> ScanResult:
            return ScanResult(success=True)

    registry.register(DisabledPlugin())
    try:
        plugin_set = PluginLoader().load_enabled(["disabled_test_plugin", "dns"])
        assert "disabled_test_plugin" in plugin_set.skipped
        assert "dns" in plugin_set.enabled
    finally:
        registry._plugins.pop("disabled_test_plugin", None)


def test_dispatcher_catches_plugin_errors() -> None:
    from app.core.scan_engine.dispatcher import ScanDispatcher
    from app.plugins.base import ScanTarget, ScannerPlugin
    from app.plugins.registry import registry

    class BrokenPlugin(ScannerPlugin):
        name = "broken_test_plugin"
        version = "0.0.1"

        def scan(self, target: ScanTarget):
            raise RuntimeError("boom")

    registry.register(BrokenPlugin())
    try:
        result = ScanDispatcher().dispatch(
            plugin_name="broken_test_plugin",
            target=ScanTarget(asset_id="1", identifier="example.com", asset_type="website"),
        )
        assert result.success is False
        assert "boom" in result.metadata.get("error", "")
    finally:
        registry._plugins.pop("broken_test_plugin", None)
