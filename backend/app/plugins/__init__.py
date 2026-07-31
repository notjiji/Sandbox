from importlib import import_module

from app.plugins.base import ScannerPlugin
from app.plugins.registry import PluginRegistry

# Built-in plugins — new plugin packages drop in here automatically.
BUILTIN_PLUGINS: list[tuple[str, str]] = [
    ("http_headers", "app.plugins.http_headers.plugin.HttpHeadersPlugin"),
    ("ssl", "app.plugins.ssl.plugin.SslPlugin"),
    ("dns", "app.plugins.dns.plugin.DnsPlugin"),
    ("whois", "app.plugins.whois.plugin.WhoisPlugin"),
    ("ports", "app.plugins.ports.plugin.PortsPlugin"),
]


def discover_plugins(registry: PluginRegistry) -> list[str]:
    """Register all built-in scanner plugins and return their names."""
    registered: list[str] = []
    for _, path in BUILTIN_PLUGINS:
        module_path, class_name = path.rsplit(".", 1)
        module = import_module(module_path)
        plugin_cls = getattr(module, class_name)
        plugin: ScannerPlugin = plugin_cls()
        registry.register(plugin)
        registered.append(plugin.name)
    return registered


from app.plugins.interfaces import PluginInterface
from app.plugins.manager import PluginManager, manager
from app.plugins.registry import registry

__all__ = [
    "PluginInterface",
    "PluginManager",
    "PluginRegistry",
    "BUILTIN_PLUGINS",
    "discover_plugins",
    "manager",
    "registry",
]
