"""Base command abstraction for devflow."""

from abc import ABC, abstractmethod
from typing import Any


class Command(ABC):
    """Base class for all devflow commands.
    
    Commands implement specific operations like test, build, publish, etc.
    They receive an AppContext at initialization and execute via the run method.
    """
    
    name: str = ""  # Override in subclasses
    help: str = ""  # Override in subclasses
    
    def __init__(self, app: 'AppContext') -> None:
        """Initialize command with application context.
        
        Args:
            app: Application context with config, logger, etc.
        """
        self.app = app
    
    @abstractmethod
    def run(self, **kwargs: Any) -> int:
        """Execute the command.
        
        Args:
            **kwargs: Command-specific arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


# Import here to avoid circular dependency
from devflow.app import AppContext  # noqa: E402
