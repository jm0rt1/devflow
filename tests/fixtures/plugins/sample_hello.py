"""Sample devflow plugin that adds a trivial 'hello' command.

This plugin demonstrates the minimal plugin interface for devflow.
It registers a simple command that prints a greeting message.

Usage:
    After loading this plugin, the following command is available:
        devflow hello [--name NAME]

Plugin Interface:
    The register(registry, app) function is called during CLI startup.
    It receives:
    - registry: CommandRegistry to register new commands
    - app: AppContext with project configuration and utilities

Example:
    To use this plugin, add it to your devflow config:
        [tool.devflow]
        plugins = ["tests.fixtures.plugins.sample_hello"]

    Or register it via entry points in pyproject.toml:
        [project.entry-points."devflow.plugins"]
        hello = "tests.fixtures.plugins.sample_hello"
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass


class HelloCommand:
    """A trivial command that prints a greeting.

    This demonstrates how plugins can add new commands to devflow.
    The command respects global flags like --dry-run and --verbose.

    Attributes:
        name: Command name used in CLI (e.g., `devflow hello`).
        help: Help text shown in `devflow hello --help`.
    """

    name: str = "hello"
    help: str = "Print a friendly greeting message"

    def __init__(self, app: Any) -> None:
        """Initialize the command with app context.

        Args:
            app: AppContext providing access to config, logger, etc.
        """
        self.app = app

    def run(self, name: str = "World", **kwargs: Any) -> int:
        """Execute the hello command.

        Args:
            name: Name to greet. Defaults to "World".
            **kwargs: Additional arguments (for compatibility).

        Returns:
            Exit code (0 for success).
        """
        # Respect dry-run flag if available
        dry_run = getattr(self.app, "dry_run", False)
        if dry_run:
            print(f"[dry-run] Would print: Hello, {name}!")
            return 0

        print(f"Hello, {name}!")
        return 0


def register(registry: Any, app: Any) -> None:
    """Register the hello command with devflow.

    This function is called by the plugin loader during CLI startup.
    It follows the PluginSpec protocol.

    Args:
        registry: CommandRegistry for registering commands.
        app: AppContext with project configuration.
    """
    registry.register(HelloCommand)
