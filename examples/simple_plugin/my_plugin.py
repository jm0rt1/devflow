"""Example plugin for devflow.

This demonstrates how to create a simple plugin that adds a custom command.
"""

from devflow.commands.base import Command
from devflow.app import CommandRegistry, AppContext


class GreetCommand(Command):
    """A greeting command that demonstrates plugin capabilities."""
    
    name = "greet"
    help = "Greet someone by name"
    
    def run(self, name: str = "World", **kwargs) -> int:
        """Execute the greet command.
        
        Args:
            name: Name to greet (default: "World")
            **kwargs: Additional arguments
            
        Returns:
            Exit code (0 for success)
        """
        # Use the logger from app context
        self.app.logger.info(f"Preparing to greet: {name}")
        
        # Support dry-run mode
        if self.app.dry_run:
            self.app.logger.info(f"[DRY-RUN] Would print: Hello, {name}!")
            return 0
        
        # Actual greeting
        print(f"Hello, {name}!")
        self.app.logger.debug(f"Successfully greeted {name}")
        
        return 0


class InfoCommand(Command):
    """Display project information."""
    
    name = "info"
    help = "Display project information"
    
    def run(self, **kwargs) -> int:
        """Execute the info command."""
        self.app.logger.info("Project Information:")
        print(f"  Project Root: {self.app.project_root}")
        print(f"  Verbose Level: {self.app.verbose}")
        print(f"  Dry Run: {self.app.dry_run}")
        
        # Show config if available
        if self.app.config:
            print(f"  Config Keys: {list(self.app.config.keys())}")
        
        return 0


def register(registry: CommandRegistry, app: AppContext) -> None:
    """Register the example plugin commands.
    
    This is the entry point called by devflow when loading plugins.
    
    Args:
        registry: Command registry to register commands with
        app: Application context with config, logger, etc.
    """
    app.logger.debug("Loading example plugin")
    
    # Register both commands
    registry.register(GreetCommand.name, GreetCommand)
    registry.register(InfoCommand.name, InfoCommand)
    
    app.logger.info("Example plugin loaded: added 'greet' and 'info' commands")
