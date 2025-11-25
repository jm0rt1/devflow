"""Application context and runtime for devflow.

This module provides the AppContext which encapsulates:
- Project root
- Loaded configuration
- Logger
- Verbosity level
- Dry-run flag
- Command registry (placeholder for Workstream B)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devflow.config import DevflowConfig, load_config
from devflow.core.paths import ProjectRootNotFoundError, find_project_root

if TYPE_CHECKING:
    pass  # CommandRegistry will be provided by Workstream B


# Verbosity levels
VERBOSITY_QUIET = -1
VERBOSITY_DEFAULT = 0
VERBOSITY_VERBOSE = 1
VERBOSITY_DEBUG = 2


def setup_logging(verbosity: int = VERBOSITY_DEFAULT) -> logging.Logger:
    """Set up and return the devflow logger with appropriate level.

    Args:
        verbosity: Verbosity level (-1=quiet, 0=default, 1=verbose, 2=debug)

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("devflow")

    # Clear any existing handlers
    logger.handlers.clear()

    # Set level based on verbosity
    if verbosity <= VERBOSITY_QUIET:
        level = logging.WARNING
    elif verbosity == VERBOSITY_DEFAULT:
        level = logging.INFO
    elif verbosity == VERBOSITY_VERBOSE:
        level = logging.DEBUG
    else:  # VERBOSITY_DEBUG or higher
        level = logging.DEBUG

    logger.setLevel(level)

    # Create console handler with formatting
    handler = logging.StreamHandler()
    handler.setLevel(level)

    # Format with phase prefix support
    if verbosity >= VERBOSITY_DEBUG:
        formatter = logging.Formatter("%(levelname)s [%(name)s] %(message)s")
    else:
        formatter = logging.Formatter("%(message)s")

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


@dataclass
class AppContext:
    """Application context encapsulating runtime state.

    This is the central state object passed to all commands and tasks.
    Other workstreams should import and use this class, not redefine it.

    Attributes:
        project_root: Path to the project root directory.
        config: Loaded and merged DevflowConfig.
        logger: Configured logger instance.
        verbosity: Current verbosity level.
        dry_run: Whether to run in dry-run mode (no side effects).
        command_registry: Registry of available commands (provided by Workstream B).
    """

    project_root: Path
    config: DevflowConfig
    logger: logging.Logger
    verbosity: int = VERBOSITY_DEFAULT
    dry_run: bool = False
    command_registry: Any = field(default=None)  # Type: CommandRegistry from Workstream B

    @classmethod
    def create(
        cls,
        project_root: Path | str | None = None,
        config_path: Path | str | None = None,
        verbosity: int = VERBOSITY_DEFAULT,
        dry_run: bool = False,
    ) -> AppContext:
        """Create an AppContext by detecting project root and loading config.

        This is the primary factory method for creating an AppContext.

        Args:
            project_root: Override for project root path. If None, auto-detect.
            config_path: Override for config file path. If None, auto-discover.
            verbosity: Verbosity level for logging.
            dry_run: Whether to run in dry-run mode.

        Returns:
            Configured AppContext instance.

        Raises:
            ProjectRootNotFoundError: If project root cannot be detected.
        """
        # Set up logging first
        logger = setup_logging(verbosity)

        # Resolve project root
        if project_root is not None:
            root = Path(project_root).resolve()
            if not root.exists():
                raise FileNotFoundError(f"Specified project root does not exist: {root}")
        else:
            try:
                root = find_project_root()
            except ProjectRootNotFoundError:
                # If no project root found and we're in a directory without markers,
                # use current directory but warn
                root = Path.cwd().resolve()
                logger.warning(
                    f"No project root markers found, using current directory: {root}"
                )

        # Resolve config path if provided
        explicit_config = Path(config_path).resolve() if config_path else None

        # Load configuration
        config = load_config(root, explicit_config)

        return cls(
            project_root=root,
            config=config,
            logger=logger,
            verbosity=verbosity,
            dry_run=dry_run,
        )

    def log(self, message: str, phase: str | None = None) -> None:
        """Log a message with optional phase prefix.

        Args:
            message: The message to log.
            phase: Optional phase prefix (e.g., 'test', 'build').
        """
        if phase:
            self.logger.info(f"[{phase}] {message}")
        else:
            self.logger.info(message)

    def debug(self, message: str, phase: str | None = None) -> None:
        """Log a debug message with optional phase prefix.

        Args:
            message: The message to log.
            phase: Optional phase prefix.
        """
        if phase:
            self.logger.debug(f"[{phase}] {message}")
        else:
            self.logger.debug(message)

    def error(self, message: str, phase: str | None = None) -> None:
        """Log an error message with optional phase prefix.

        Args:
            message: The error message to log.
            phase: Optional phase prefix.
        """
        if phase:
            self.logger.error(f"[{phase}] {message}")
        else:
            self.logger.error(message)

    def warning(self, message: str, phase: str | None = None) -> None:
        """Log a warning message with optional phase prefix.

        Args:
            message: The warning message to log.
            phase: Optional phase prefix.
        """
        if phase:
            self.logger.warning(f"[{phase}] {message}")
        else:
            self.logger.warning(message)
