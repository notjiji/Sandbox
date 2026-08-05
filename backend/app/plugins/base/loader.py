"""Discover built-in scanner plugins and select plugins for a scan."""

from dataclasses import dataclass

from app.core.exceptions import ValidationAppError
from app.plugins.base.plugin import ScannerPlugin
from app.plugins.base.registry import PluginRegistry, registry
from app.plugins.cookies.plugin import CookiesPlugin
from app.plugins.dns.plugin import DnsPlugin
from app.plugins.future.cloud.plugin import CloudPlugin
from app.plugins.future.cve.plugin import CvePlugin
from app.plugins.future.kubernetes.plugin import KubernetesPlugin
from app.plugins.future.malware.plugin import MalwarePlugin
from app.plugins.http_headers.plugin import HttpHeadersPlugin
from app.plugins.ports.plugin import PortsPlugin
from app.plugins.robots.plugin import RobotsPlugin
from app.plugins.ssl.plugin import SslPlugin
from app.plugins.tls.plugin import TlsPlugin
from app.plugins.whois.plugin import WhoisPlugin
from app.scans.profiles import resolve_profile_plugins

BUILTIN_PLUGIN_CLASSES: list[type[ScannerPlugin]] = [
    HttpHeadersPlugin,
    SslPlugin,
    TlsPlugin,
    DnsPlugin,
    WhoisPlugin,
    PortsPlugin,
    RobotsPlugin,
    CookiesPlugin,
    MalwarePlugin,
    CloudPlugin,
    KubernetesPlugin,
    CvePlugin,
]


@dataclass(frozen=True)
class PluginSelection:
    enabled: list[ScannerPlugin]
    skipped: list[str]


class PluginLoader:
    """Discovers built-in plugins and resolves which run for a scan profile."""

    def __init__(self, plugin_registry: PluginRegistry | None = None) -> None:
        self._registry = plugin_registry or registry

    def discover(self) -> list[str]:
        """Register all built-in plugins if the registry is empty."""
        if self._registry.list_names():
            return self._registry.list_names()

        registered: list[str] = []
        for plugin_cls in BUILTIN_PLUGIN_CLASSES:
            plugin = plugin_cls()
            self._registry.register(plugin)
            registered.append(plugin.name)
        return registered

    def select_for_scan(self, scan) -> PluginSelection:
        """Resolve enabled plugins for a scan from its profile."""
        self.discover()
        plugin_names = resolve_profile_plugins(scan.scan_type, scan.selected_plugins)
        enabled, missing = self._registry.resolve_plugin_names(plugin_names)
        if scan.scan_type.value != "custom" and missing:
            raise ValidationAppError(f"Profile plugin(s) unavailable: {', '.join(missing)}")
        if scan.scan_type.value == "custom" and not enabled:
            raise ValidationAppError("None of the selected plugins are available")
        disabled = [plugin.name for plugin in self._registry.get_disabled_plugins()]
        return PluginSelection(enabled=enabled, skipped=missing + disabled)


plugin_loader = PluginLoader()
