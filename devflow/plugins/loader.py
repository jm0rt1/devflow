"""Plugin discovery and loading for devflow.

This module handles:
1. Discovering plugins from entry points (devflow.plugins group)
2. Discovering plugins from config-provided module paths
3. Loading and registering plugins with failure isolation

Precedence Rules:
    - Entry point plugins are discovered first (priority 0)
    - Config plugins are discovered second (priority 100)
    - If two plugins have the same name, the higher priority one wins
    - This allows config to override or disable entry point plugins

Failure Isolation:
    - Plugin discovery failures are logged but don't crash the CLI
    - Plugin import failures are logged but don't crash the CLI
    - Plugin registration failures are logged but don't crash the CLI
    - Each plugin is isolated: one bad plugin won't affect others
"""

from __future__ import annotations

import importlib
import logging
import sys
from typing import TYPE_CHECKING, Any, Callable

from devflow.plugins.interface import PluginError, PluginMetadata

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Entry point group for plugin discovery
ENTRY_POINT_GROUP = "devflow.plugins"

# Priority levels for plugin sources
PRIORITY_ENTRY_POINT = 0
PRIORITY_CONFIG = 100


def discover_entry_point_plugins() -> list[PluginMetadata]:
    """Discover plugins registered via entry points.

    Looks for entry points in the 'devflow.plugins' group.
    Each entry point should point to a module with a `register` function.

    Returns:
        List of PluginMetadata for discovered plugins.

    Example pyproject.toml entry point configuration:
        ```toml
        [project.entry-points."devflow.plugins"]
        my-plugin = "my_plugin"
        ```
    """
    plugins: list[PluginMetadata] = []

    # Use importlib.metadata for entry point discovery (Python 3.9+)
    if sys.version_info >= (3, 10):
        from importlib.metadata import entry_points

        eps = entry_points(group=ENTRY_POINT_GROUP)
    else:
        from importlib.metadata import entry_points

        all_eps = entry_points()
        eps = all_eps.get(ENTRY_POINT_GROUP, [])

    for ep in eps:
        try:
            # Entry point value is the module path
            plugins.append(
                PluginMetadata(
                    name=ep.name,
                    module_path=ep.value,
                    source="entry_point",
                    priority=PRIORITY_ENTRY_POINT,
                )
            )
            logger.debug(f"Discovered entry point plugin: {ep.name} -> {ep.value}")
        except Exception as e:
            logger.warning(f"Failed to read entry point '{ep.name}': {e}")

    return plugins


def discover_config_plugins(plugin_modules: list[str] | None) -> list[PluginMetadata]:
    """Discover plugins from config-provided module paths.

    Plugins can be specified in the devflow config under [tool.devflow.plugins]
    or as a list of module paths.

    Args:
        plugin_modules: List of module paths from config.
                       Example: ["my_plugin", "another_plugin.commands"]

    Returns:
        List of PluginMetadata for discovered plugins.

    Example config:
        ```toml
        [tool.devflow]
        plugins = ["my_local_plugin", "my_company.devflow_extensions"]
        ```
    """
    if not plugin_modules:
        return []

    plugins: list[PluginMetadata] = []
    for idx, module_path in enumerate(plugin_modules):
        # Derive name from module path (last component)
        name = module_path.split(".")[-1]
        plugins.append(
            PluginMetadata(
                name=name,
                module_path=module_path,
                source="config",
                # Config plugins get increasing priority to maintain order
                priority=PRIORITY_CONFIG + idx,
            )
        )
        logger.debug(f"Discovered config plugin: {name} -> {module_path}")

    return plugins


def _merge_plugins(
    entry_point_plugins: list[PluginMetadata],
    config_plugins: list[PluginMetadata],
) -> list[PluginMetadata]:
    """Merge plugins from different sources with precedence rules.

    Config plugins take precedence over entry point plugins with the same name.
    This allows users to override or replace built-in plugin behavior.

    Args:
        entry_point_plugins: Plugins from entry points.
        config_plugins: Plugins from config.

    Returns:
        Merged list of plugins with duplicates resolved by precedence.
    """
    # Build a dict keyed by name, higher priority overwrites
    plugin_map: dict[str, PluginMetadata] = {}

    for plugin in entry_point_plugins + config_plugins:
        existing = plugin_map.get(plugin.name)
        if existing is None or plugin.priority > existing.priority:
            if existing is not None:
                logger.debug(
                    f"Plugin '{plugin.name}' from {plugin.source} "
                    f"overrides plugin from {existing.source}"
                )
            plugin_map[plugin.name] = plugin

    # Return sorted by priority for deterministic load order
    return sorted(plugin_map.values(), key=lambda p: (p.priority, p.name))


def _load_plugin_module(
    metadata: PluginMetadata,
) -> Callable[[Any, Any], None] | None:
    """Load a plugin module and return its register function.

    Args:
        metadata: Plugin metadata containing module path.

    Returns:
        The register function if found, None otherwise.

    Raises:
        PluginError: If the module cannot be loaded or lacks a register function.
    """
    try:
        module = importlib.import_module(metadata.module_path)
    except ImportError as e:
        raise PluginError(
            metadata.name,
            f"Failed to import module '{metadata.module_path}'",
            cause=e,
        ) from e
    except Exception as e:
        raise PluginError(
            metadata.name,
            f"Error loading module '{metadata.module_path}': {e}",
            cause=e,
        ) from e

    register_fn = getattr(module, "register", None)
    if register_fn is None:
        raise PluginError(
            metadata.name,
            f"Module '{metadata.module_path}' has no 'register' function",
        )

    if not callable(register_fn):
        raise PluginError(
            metadata.name,
            f"'register' in '{metadata.module_path}' is not callable",
        )

    return register_fn


def _call_register(
    metadata: PluginMetadata,
    register_fn: Callable[[Any, Any], None],
    registry: Any,
    app: Any,
) -> None:
    """Call a plugin's register function with error handling.

    Args:
        metadata: Plugin metadata.
        register_fn: The plugin's register function.
        registry: CommandRegistry to pass to the plugin.
        app: AppContext to pass to the plugin.

    Raises:
        PluginError: If registration fails.
    """
    try:
        register_fn(registry, app)
    except PluginError:
        raise
    except Exception as e:
        raise PluginError(
            metadata.name,
            f"Error during registration: {e}",
            cause=e,
        ) from e


class PluginLoadResult:
    """Result of loading plugins.

    Attributes:
        loaded: List of successfully loaded plugin names.
        failed: Dict mapping plugin names to their PluginError.
    """

    def __init__(self) -> None:
        self.loaded: list[str] = []
        self.failed: dict[str, PluginError] = {}

    @property
    def success_count(self) -> int:
        """Number of successfully loaded plugins."""
        return len(self.loaded)

    @property
    def failure_count(self) -> int:
        """Number of plugins that failed to load."""
        return len(self.failed)

    def __repr__(self) -> str:
        return (
            f"PluginLoadResult(loaded={self.loaded}, "
            f"failed={list(self.failed.keys())})"
        )


def load_all_plugins(
    registry: Any,
    app: Any,
    plugin_modules: list[str] | None = None,
) -> PluginLoadResult:
    """Discover and load all plugins.

    This is the main entry point for the plugin system. It:
    1. Discovers plugins from entry points
    2. Discovers plugins from config
    3. Merges them with precedence rules
    4. Loads and registers each plugin
    5. Isolates failures so bad plugins don't crash the CLI

    Args:
        registry: CommandRegistry instance for plugins to register commands.
        app: AppContext instance providing project context.
        plugin_modules: Optional list of module paths from config.

    Returns:
        PluginLoadResult with lists of loaded and failed plugins.

    Example:
        ```python
        from devflow.plugins import load_all_plugins

        result = load_all_plugins(registry, app, config.plugins)
        if result.failure_count > 0:
            for name, error in result.failed.items():
                logger.warning(f"Plugin {name} failed: {error.message}")
        ```
    """
    result = PluginLoadResult()

    # Discover plugins from all sources
    entry_point_plugins = discover_entry_point_plugins()
    config_plugins = discover_config_plugins(plugin_modules)

    # Merge with precedence
    all_plugins = _merge_plugins(entry_point_plugins, config_plugins)

    logger.debug(f"Loading {len(all_plugins)} plugins")

    # Load each plugin with isolation
    for metadata in all_plugins:
        try:
            register_fn = _load_plugin_module(metadata)
            if register_fn is not None:
                _call_register(metadata, register_fn, registry, app)
                result.loaded.append(metadata.name)
                logger.info(f"Loaded plugin: {metadata.name}")
        except PluginError as e:
            result.failed[metadata.name] = e
            logger.error(f"Failed to load plugin '{metadata.name}': {e.message}")
            if e.cause:
                logger.debug(f"Cause: {e.cause}")
        except Exception as e:
            error = PluginError(metadata.name, f"Unexpected error: {e}", cause=e)
            result.failed[metadata.name] = error
            logger.error(f"Failed to load plugin '{metadata.name}': {e}")

    return result
