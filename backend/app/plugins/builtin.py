"""Built-in scanner plugins registered at startup."""

from app.plugins.dns.plugin import DnsPlugin
from app.plugins.http_headers.plugin import HttpHeadersPlugin
from app.plugins.ports.plugin import PortsPlugin
from app.plugins.registry import PluginRegistry
from app.plugins.ssl.plugin import SslPlugin
from app.plugins.whois.plugin import WhoisPlugin

BUILTIN_PLUGIN_CLASSES = [
    HttpHeadersPlugin,
    SslPlugin,
    DnsPlugin,
    WhoisPlugin,
    PortsPlugin,
]


def discover_plugins(registry: PluginRegistry) -> list[str]:
    """Register all built-in scanner plugins and return their slugs."""
    registered: list[str] = []
    for plugin_cls in BUILTIN_PLUGIN_CLASSES:
        plugin = plugin_cls()
        registry.register(plugin)
        registered.append(plugin.name)
    return registered
