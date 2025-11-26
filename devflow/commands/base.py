"""Command base class and registry for devflow.

This module provides the foundational abstractions for defining and registering
commands in the devflow CLI tool. Other workstreams register their commands
through the hooks provided here.

Ownership: Workstream B (task/registry)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    # AppContext is owned by Workstream A - we only type hint it
    from typing import Protocol

    class AppContext(Protocol):
        """Protocol for AppContext (owned by Workstream A).

        This is a minimal protocol to allow type checking without
        creating a dependency on the actual implementation.
        """

        project_root: Any
        config: Any
        dry_run: bool
        verbosity: int


class Command(ABC):
    """Abstract base class for devflow commands.

    All commands in devflow inherit from this base class and implement
    the run() method. Commands are registered with the CommandRegistry
    and dispatched by the CLI.

    Attributes:
        name: The command name used in the CLI (e.g., 'test', 'build').
        help: Short help text displayed in --help output.

    Example:
        >>> class TestCommand(Command):
        ...     name = "test"
        ...     help = "Run project tests"
        ...
        ...     def run(self, **kwargs) -> int:
        ...         # Implementation
        ...         return 0
    """

    name: str
    help: str

    def __init__(self, app: AppContext) -> None:
        """Initialize the command with application context.

        Args:
            app: The application context containing config, project root,
                 verbosity settings, and dry-run flag.
        """
        self.app = app

    @abstractmethod
    def run(self, **kwargs: Any) -> int:
        """Execute the command.

        Args:
            **kwargs: Command-specific arguments passed from the CLI.

        Returns:
            Exit code: 0 for success, non-zero for failure.
        """
        ...


class CommandRegistry:
    """Registry for mapping command names to handler classes.

    The registry maintains a mapping of string command names to their
    corresponding Command subclasses. It supports registration of built-in
    commands, plugin commands, and config-defined custom tasks.

    Example:
        >>> registry = CommandRegistry()
        >>> registry.register(TestCommand)
        >>> cmd_cls = registry.get("test")
        >>> cmd = cmd_cls(app_context)
        >>> exit_code = cmd.run()
    """

    def __init__(self) -> None:
        """Initialize an empty command registry."""
        self._commands: dict[str, type[Command]] = {}

    def register(self, cmd_cls: type[Command]) -> None:
        """Register a command class.

        Args:
            cmd_cls: A Command subclass to register. Must have a `name` attribute.

        Raises:
            ValueError: If a command with the same name is already registered.
        """
        if cmd_cls.name in self._commands:
            raise ValueError(
                f"Command '{cmd_cls.name}' is already registered. "
                "Use a different name or unregister the existing command first."
            )
        self._commands[cmd_cls.name] = cmd_cls

    def unregister(self, name: str) -> bool:
        """Unregister a command by name.

        Args:
            name: The name of the command to unregister.

        Returns:
            True if the command was unregistered, False if not found.
        """
        if name in self._commands:
            del self._commands[name]
            return True
        return False

    def get(self, name: str) -> type[Command] | None:
        """Get a command class by name.

        Args:
            name: The name of the command to retrieve.

        Returns:
            The Command subclass if found, None otherwise.
        """
        return self._commands.get(name)

    def list_commands(self) -> list[str]:
        """List all registered command names.

        Returns:
            Sorted list of registered command names.
        """
        return sorted(self._commands.keys())

    def __contains__(self, name: str) -> bool:
        """Check if a command is registered.

        Args:
            name: The command name to check.

        Returns:
            True if the command is registered, False otherwise.
        """
        return name in self._commands

    def __len__(self) -> int:
        """Return the number of registered commands."""
        return len(self._commands)
