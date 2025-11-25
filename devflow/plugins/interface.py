"""Plugin interface definitions for devflow.

This module defines the protocol that plugins must follow and related types.

Plugins are expected to provide a `register(registry, app)` function that:
- Accepts a CommandRegistry for registering new commands
- Accepts an AppContext for accessing project configuration and utilities
- May raise PluginError if registration fails for a known reason
- Should not raise other exceptions (they will be caught and logged)

Lifecycle Expectations:
    1. Plugins are discovered during CLI startup
    2. Plugin modules are imported
    3. The `register()` function is called exactly once per plugin
    4. Registration should be fast and not perform heavy I/O
    5. Commands registered by plugins are available alongside built-in commands
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, runtime_checkable, Any

if TYPE_CHECKING:
    pass


class PluginError(Exception):
    """Raised when a plugin fails to load or register.

    This exception is caught by the plugin loader and logged as an error.
    The CLI will continue to function without the failed plugin.

    Attributes:
        plugin_name: Name of the plugin that failed.
        message: Description of what went wrong.
        cause: Optional underlying exception that caused the failure.
    """

    def __init__(
        self,
        plugin_name: str,
        message: str,
        cause: Exception | None = None,
    ) -> None:
        self.plugin_name = plugin_name
        self.message = message
        self.cause = cause
        super().__init__(f"Plugin '{plugin_name}' failed: {message}")


@runtime_checkable
class PluginSpec(Protocol):
    """Protocol defining the plugin interface.

    A plugin module must provide a `register` function matching this signature.
    The function is called during CLI startup to allow the plugin to register
    its commands and tasks.

    The registry and app parameters are provided by the core devflow system:
    - registry: Used to register new Command classes (see devflow.commands.base)
    - app: Provides access to project root, config, logger, dry-run flag, etc.

    Example:
        ```python
        # my_plugin/__init__.py
        from devflow.plugins import PluginSpec

        def register(registry, app) -> None:
            from my_plugin.commands import MyCustomCommand
            registry.register(MyCustomCommand)
        ```

    Notes:
        - The register function should not perform expensive operations
        - Errors during registration should raise PluginError
        - The function must not block or perform network I/O
        - Commands registered should respect global flags (--dry-run, --verbose)
    """

    def register(self, registry: Any, app: Any) -> None:
        """Register plugin commands and tasks.

        Args:
            registry: CommandRegistry instance for registering commands.
                      See devflow.commands.base.CommandRegistry (Workstream B).
            app: AppContext instance providing project context.
                 See devflow.app.AppContext (Workstream A).
        """
        ...


class PluginMetadata:
    """Metadata about a discovered plugin.

    Attributes:
        name: Unique name identifying the plugin.
        module_path: Python module path to import.
        source: How the plugin was discovered ('entry_point' or 'config').
        priority: Load order priority (lower = earlier, entry_points=0, config=100).
    """

    def __init__(
        self,
        name: str,
        module_path: str,
        source: str,
        priority: int = 0,
    ) -> None:
        self.name = name
        self.module_path = module_path
        self.source = source
        self.priority = priority

    def __repr__(self) -> str:
        return (
            f"PluginMetadata(name={self.name!r}, module_path={self.module_path!r}, "
            f"source={self.source!r}, priority={self.priority})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, PluginMetadata):
            return NotImplemented
        return (
            self.name == other.name
            and self.module_path == other.module_path
            and self.source == other.source
        )

    def __hash__(self) -> int:
        return hash((self.name, self.module_path, self.source))
