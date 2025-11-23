"""Application context and runtime."""

from pathlib import Path

from devflow.config import load_config
from devflow.core.logging import Logger, LogLevel
from devflow.core.paths import find_project_root


class AppContext:
    """Central application context containing configuration and runtime state."""

    def __init__(
        self,
        project_root: Path | None = None,
        config_path: Path | None = None,
        verbosity: int = 1,
        quiet: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize application context.

        Args:
            project_root: Project root directory. If None, auto-detected.
            config_path: Explicit config file path. If None, auto-discovered.
            verbosity: Verbosity level (0=quiet, 1=normal, 2=verbose, 3=debug)
            quiet: Quiet mode flag
            dry_run: Dry-run mode flag
        """
        # Determine log level
        if quiet:
            log_level = LogLevel.QUIET
        else:
            log_level = LogLevel(min(verbosity, 3))

        self.logger = Logger(level=log_level)
        self.dry_run = dry_run

        # Find or use project root
        if project_root:
            self.project_root = project_root.resolve()
        else:
            self.project_root = find_project_root()

        self.logger.debug(f"Project root: {self.project_root}")

        # Load configuration
        self.config = load_config(self.project_root, config_path)

        if dry_run:
            self.logger.info("Running in DRY-RUN mode - no changes will be made")

    @property
    def venv_path(self) -> Path:
        """Get the virtual environment path."""
        return self.project_root / self.config.venv_dir
