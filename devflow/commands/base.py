"""Base command abstraction and registry."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Type

from devflow.app import AppContext


class Command(ABC):
    """Base class for devflow commands."""

    name: str = ""
    help: str = ""

    def __init__(self, app: AppContext) -> None:
        """
        Initialize command with app context.
        
        Args:
            app: Application context
        """
        self.app = app

    @abstractmethod
    def run(self, **kwargs) -> int:
        """
        Execute the command.
        
        Args:
            **kwargs: Command-specific arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


class CommandRegistry:
    """Registry for managing available commands."""

    def __init__(self) -> None:
        self._commands: Dict[str, Type[Command]] = {}

    def register(self, cmd_cls: Type[Command]) -> None:
        """
        Register a command class.
        
        Args:
            cmd_cls: Command class to register
        """
        self._commands[cmd_cls.name] = cmd_cls

    def get(self, name: str) -> Optional[Type[Command]]:
        """
        Get a command class by name.
        
        Args:
            name: Command name
            
        Returns:
            Command class or None if not found
        """
        return self._commands.get(name)

    def list_commands(self) -> Dict[str, str]:
        """
        List all registered commands with their help text.
        
        Returns:
            Dictionary mapping command names to help text
        """
        return {name: cmd.help for name, cmd in sorted(self._commands.items())}
