"""Plugin system for devflow.

Plugins can extend devflow by registering new commands or tasks.
Plugins are discovered via:
1. Entry points in the 'devflow.plugins' group
2. Module paths specified in config under [tool.devflow.plugins]

Plugin Interface:
    Each plugin must implement a `register` function with signature:
        def register(registry: CommandRegistry, app: AppContext) -> None
    
    The register function should:
    - Register new commands via registry.register(name, CommandClass)
    - Optionally modify app context (e.g., add config defaults)
    - Handle any setup/initialization needed
    
    Example:
        from devflow.commands.base import Command
        
        class MyCommand(Command):
            name = "mycmd"
            help = "My custom command"
            
            def run(self, **kwargs):
                self.app.logger.info("Running my command!")
                return 0
        
        def register(registry, app):
            registry.register(MyCommand.name, MyCommand)
"""

import importlib
import importlib.metadata
import sys
from typing import Any, Callable

from devflow.app import AppContext, CommandRegistry


PluginRegisterFunc = Callable[[CommandRegistry, AppContext], None]


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginLoadError(PluginError):
    """Raised when a plugin fails to load."""
    pass


class PluginRegistrationError(PluginError):
    """Raised when a plugin fails to register properly."""
    pass


def discover_entry_point_plugins() -> list[tuple[str, PluginRegisterFunc]]:
    """Discover plugins via entry points in the 'devflow.plugins' group.
    
    Returns:
        List of (plugin_name, register_function) tuples
    """
    plugins: list[tuple[str, PluginRegisterFunc]] = []
    
    try:
        # Get all entry points in the 'devflow.plugins' group
        entry_points = importlib.metadata.entry_points()
        
        # Handle both dict-style (Python 3.9) and SelectableGroups (Python 3.10+)
        if hasattr(entry_points, 'select'):
            # Python 3.10+
            plugin_eps = entry_points.select(group='devflow.plugins')
        else:
            # Python 3.9
            plugin_eps = entry_points.get('devflow.plugins', [])
        
        for ep in plugin_eps:
            try:
                register_func = ep.load()
                if not callable(register_func):
                    raise PluginLoadError(
                        f"Plugin '{ep.name}' entry point must be a callable, "
                        f"got {type(register_func)}"
                    )
                plugins.append((ep.name, register_func))
            except Exception as e:
                # Log but don't crash - bad plugins should fail gracefully
                print(f"Warning: Failed to load plugin '{ep.name}': {e}", file=sys.stderr)
    except Exception as e:
        # Entry point discovery itself failed - log but continue
        print(f"Warning: Failed to discover entry point plugins: {e}", file=sys.stderr)
    
    return plugins


def discover_config_plugins(config: dict[str, Any]) -> list[tuple[str, PluginRegisterFunc]]:
    """Discover plugins via module paths in config.
    
    Config format:
        [tool.devflow.plugins]
        modules = ["mypackage.plugin", "another.plugin"]
    
    Args:
        config: Application configuration dict
        
    Returns:
        List of (plugin_name, register_function) tuples
    """
    plugins: list[tuple[str, PluginRegisterFunc]] = []
    
    # Get plugin configuration
    plugin_config = config.get('plugins', {})
    module_paths = plugin_config.get('modules', [])
    
    if not isinstance(module_paths, list):
        print(
            f"Warning: config plugins.modules must be a list, got {type(module_paths)}",
            file=sys.stderr
        )
        return plugins
    
    for module_path in module_paths:
        if not isinstance(module_path, str):
            print(
                f"Warning: plugin module path must be string, got {type(module_path)}",
                file=sys.stderr
            )
            continue
        
        try:
            # Import the module
            module = importlib.import_module(module_path)
            
            # Get the register function
            if not hasattr(module, 'register'):
                raise PluginLoadError(
                    f"Plugin module '{module_path}' must define a 'register' function"
                )
            
            register_func = getattr(module, 'register')
            if not callable(register_func):
                raise PluginLoadError(
                    f"Plugin '{module_path}' register must be callable, "
                    f"got {type(register_func)}"
                )
            
            plugins.append((module_path, register_func))
        except Exception as e:
            # Log but don't crash - bad plugins should fail gracefully
            print(f"Warning: Failed to load plugin '{module_path}': {e}", file=sys.stderr)
    
    return plugins


def load_plugins(app: AppContext) -> None:
    """Load and register all discovered plugins.
    
    Plugins are loaded in this order:
    1. Entry point plugins (from setuptools entry_points)
    2. Config-defined plugins (from [tool.devflow.plugins])
    
    If a plugin name appears in both sources, the config-defined one takes precedence.
    
    Args:
        app: Application context with registry and config
        
    Raises:
        RuntimeError: If app.command_registry is None
    """
    if app.command_registry is None:
        raise RuntimeError("AppContext must have a command_registry before loading plugins")
    
    registry = app.command_registry
    loaded_plugins: dict[str, str] = {}  # name -> source
    
    # Discover all plugins
    entry_point_plugins = discover_entry_point_plugins()
    config_plugins = discover_config_plugins(app.config)
    
    # Load entry point plugins first
    for plugin_name, register_func in entry_point_plugins:
        try:
            register_func(registry, app)
            loaded_plugins[plugin_name] = "entry_point"
            app.logger.debug(f"Loaded plugin '{plugin_name}' from entry point")
        except Exception as e:
            # Bad plugin - log error but continue
            app.logger.error(f"Failed to register plugin '{plugin_name}': {e}")
    
    # Load config plugins (these take precedence)
    for plugin_name, register_func in config_plugins:
        try:
            # If already loaded from entry point, this overrides it
            if plugin_name in loaded_plugins:
                app.logger.debug(
                    f"Plugin '{plugin_name}' from config overrides "
                    f"{loaded_plugins[plugin_name]} version"
                )
            
            register_func(registry, app)
            loaded_plugins[plugin_name] = "config"
            app.logger.debug(f"Loaded plugin '{plugin_name}' from config")
        except Exception as e:
            # Bad plugin - log error but continue
            app.logger.error(f"Failed to register plugin '{plugin_name}': {e}")
    
    app.logger.info(f"Loaded {len(loaded_plugins)} plugin(s)")
