"""Sample plugin for testing plugin system.

This plugin adds a simple "hello" command to demonstrate plugin capabilities.
"""

from devflow.commands.base import Command
from devflow.app import CommandRegistry, AppContext


class HelloCommand(Command):
    """A simple hello world command added by a plugin."""
    
    name = "hello"
    help = "Say hello (added by sample plugin)"
    
    def run(self, **kwargs) -> int:
        """Execute the hello command."""
        name = kwargs.get('name', 'World')
        
        if self.app.dry_run:
            self.app.logger.info(f"[DRY-RUN] Would say: Hello, {name}!")
        else:
            self.app.logger.info(f"Hello, {name}!")
        
        return 0


def register(registry: CommandRegistry, app: AppContext) -> None:
    """Register the sample plugin commands.
    
    This is the entry point for the plugin system.
    
    Args:
        registry: Command registry to register commands with
        app: Application context
    """
    app.logger.debug("Registering sample plugin")
    registry.register(HelloCommand.name, HelloCommand)
