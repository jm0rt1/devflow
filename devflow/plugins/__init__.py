"""Devflow plugin system.

This module provides plugin discovery, loading, and registration for devflow.
Plugins can be discovered via:
1. Entry points (under the `devflow.plugins` group)
2. Config-provided module paths (in [tool.devflow.plugins])

Plugin Interface:
    Plugins must provide a `register(registry, app)` function that accepts:
    - registry: CommandRegistry - used to register new commands
    - app: AppContext - provides access to project config, logger, etc.

Example plugin module:
    ```python
    def register(registry, app):
        from my_plugin.commands import MyCommand
        registry.register(MyCommand)
    ```

Lifecycle:
    1. Plugin discovery happens at CLI startup
    2. Entry point plugins are loaded first
    3. Config-provided plugins are loaded second (can override entry points)
    4. Each plugin's `register()` is called with the shared registry and app
    5. If a plugin fails to load, an error is logged but the CLI continues
"""

from devflow.plugins.interface import PluginSpec, PluginError
from devflow.plugins.loader import (
    discover_entry_point_plugins,
    discover_config_plugins,
    load_all_plugins,
)

__all__ = [
    "PluginSpec",
    "PluginError",
    "discover_entry_point_plugins",
    "discover_config_plugins",
    "load_all_plugins",
]
