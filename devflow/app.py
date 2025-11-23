"""Application context for devflow."""

from pathlib import Path
from typing import Optional

from devflow.config.loader import load_config
from devflow.core.logging import DevFlowLogger
from devflow.core.paths import find_project_root
from devflow.core.subprocess import SubprocessRunner


class AppContext:
    """
    Central application context holding project state and configuration.
    """

    def __init__(
        self,
        project_root: Optional[Path] = None,
        config_path: Optional[Path] = None,
        verbosity: int = 0,
        quiet: bool = False,
        dry_run: bool = False,
    ):
        """
        Initialize application context.

        Args:
            project_root: Optional explicit project root
            config_path: Optional explicit config file path
            verbosity: Verbosity level (0=INFO, 1+=DEBUG)
            quiet: If True, suppress most output
            dry_run: If True, don't execute destructive operations
        """
        # Find project root
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            self.project_root = find_project_root()

        # Initialize logger
        self.logger = DevFlowLogger(verbosity=verbosity, quiet=quiet)

        # Load configuration
        self.config = load_config(
            project_root=self.project_root,
            config_path=Path(config_path) if config_path else None,
        )

        # Store settings
        self.dry_run = dry_run
        self.verbosity = verbosity
        self.quiet = quiet

        # Create subprocess runner
        self.runner = SubprocessRunner(
            logger=self.logger,
            dry_run=dry_run,
            cwd=self.project_root,
        )

        # Log initialization
        self.logger.debug(f"Project root: {self.project_root}")
        self.logger.debug(f"Venv directory: {self.venv_dir}")

    @property
    def venv_dir(self) -> Path:
        """Get the virtual environment directory path."""
        return self.project_root / self.config.venv_dir

    @property
    def dist_dir(self) -> Path:
        """Get the distribution directory path."""
        return self.project_root / self.config.paths.dist_dir

    def venv_exists(self) -> bool:
        """Check if virtual environment exists."""
        from devflow.core.paths import get_venv_python

        venv_python = get_venv_python(self.venv_dir)
        return venv_python.exists()
