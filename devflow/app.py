"""Application context and runtime state."""

import logging
import sys
from dataclasses import dataclass, field
from pathlib import Path

from devflow.config import DevflowConfig, load_config


@dataclass
class AppContext:
    """
    Central application context holding project state and configuration.

    Attributes:
        project_root: Path to the project root directory.
        config: Loaded configuration.
        verbose: Verbosity level (0=normal, 1=-v, 2=-vv).
        quiet: Whether to suppress non-error output.
        dry_run: Whether to run in dry-run mode.
        logger: Configured logger instance.
    """

    project_root: Path
    config: DevflowConfig
    verbose: int = 0
    quiet: bool = False
    dry_run: bool = False
    logger: logging.Logger = field(init=False)

    def __post_init__(self):
        """Initialize the logger after dataclass initialization."""
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure and return a logger with appropriate verbosity."""
        logger = logging.getLogger("devflow")

        # Clear any existing handlers
        logger.handlers.clear()

        # Set level based on verbosity/quiet
        if self.quiet:
            logger.setLevel(logging.ERROR)
        elif self.verbose >= 2:
            logger.setLevel(logging.DEBUG)
        elif self.verbose >= 1:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.WARNING)

        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)

        # Create formatter
        if self.verbose >= 2:
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        else:
            formatter = logging.Formatter("[%(levelname)s] %(message)s")

        handler.setFormatter(formatter)
        logger.addHandler(handler)

        return logger

    @classmethod
    def create(
        cls,
        config_path: Path | None = None,
        project_root: Path | None = None,
        verbose: int = 0,
        quiet: bool = False,
        dry_run: bool = False,
    ) -> "AppContext":
        """
        Create an AppContext with loaded configuration.

        Args:
            config_path: Optional explicit config file path.
            project_root: Optional explicit project root path.
            verbose: Verbosity level.
            quiet: Quiet mode flag.
            dry_run: Dry-run mode flag.

        Returns:
            Initialized AppContext.
        """
        # Load configuration
        config = load_config(config_path=config_path, project_root=project_root)

        # Determine project root
        if project_root is None:
            from devflow.core.paths import find_project_root

            try:
                project_root = find_project_root()
            except RuntimeError:
                # If no project root found, use current directory
                project_root = Path.cwd()

        return cls(
            project_root=project_root,
            config=config,
            verbose=verbose,
            quiet=quiet,
            dry_run=dry_run,
        )
