"""Application context and core runtime for devflow."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import logging
import sys


@dataclass
class AppContext:
    """Central application context holding configuration, state, and services.
    
    This is passed to commands and plugins to give them access to:
    - Project root and configuration
    - Logger with verbosity settings
    - Dry-run mode
    - Command registry
    """
    
    project_root: Path
    config: dict[str, Any] = field(default_factory=dict)
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger("devflow"))
    verbose: int = 0  # Verbosity level: 0=normal, 1=-v, 2=-vv, etc.
    quiet: bool = False
    dry_run: bool = False
    command_registry: Optional['CommandRegistry'] = None
    
    def __post_init__(self) -> None:
        """Configure logger based on verbosity settings."""
        if self.quiet:
            self.logger.setLevel(logging.WARNING)
        elif self.verbose >= 2:
            self.logger.setLevel(logging.DEBUG)
        elif self.verbose >= 1:
            self.logger.setLevel(logging.INFO)
        else:
            self.logger.setLevel(logging.INFO)
        
        # Add console handler if not already present
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('[%(levelname)s] %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)


class CommandRegistry:
    """Registry for mapping command names to command classes.
    
    Commands and plugins register themselves here during initialization.
    """
    
    def __init__(self) -> None:
        self._commands: dict[str, type['Command']] = {}
    
    def register(self, name: str, command_cls: type['Command']) -> None:
        """Register a command class under a given name.
        
        Args:
            name: Command name (e.g., "test", "build")
            command_cls: Command class to register
            
        Raises:
            ValueError: If command name is already registered
        """
        if name in self._commands:
            raise ValueError(f"Command '{name}' is already registered")
        self._commands[name] = command_cls
    
    def get(self, name: str) -> Optional[type['Command']]:
        """Get a command class by name.
        
        Args:
            name: Command name to look up
            
        Returns:
            Command class or None if not found
        """
        return self._commands.get(name)
    
    def list_commands(self) -> list[str]:
        """List all registered command names.
        
        Returns:
            Sorted list of command names
        """
        return sorted(self._commands.keys())


# Import here to avoid circular dependency
from devflow.commands.base import Command  # noqa: E402
