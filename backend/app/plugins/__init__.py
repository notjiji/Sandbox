from app.plugins.base import ScannerPlugin
from app.plugins.builtin import BUILTIN_PLUGIN_CLASSES, discover_plugins
from app.plugins.interfaces import PluginInterface
from app.plugins.manager import PluginManager, manager
from app.plugins.registry import PluginRegistry, registry

__all__ = [
    "PluginInterface",
    "PluginManager",
    "PluginRegistry",
    "ScannerPlugin",
    "BUILTIN_PLUGIN_CLASSES",
    "discover_plugins",
    "manager",
    "registry",
]
