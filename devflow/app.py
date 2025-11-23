"""Application context for devflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from devflow.config import DevflowConfig, load_config
from devflow.core.logging import DevflowLogger
from devflow.core.paths import find_project_root


@dataclass
class AppContext:
    """
    Application context holding project configuration and runtime state.

    Attributes:
        project_root: Path to the project root directory
        config: Loaded devflow configuration
        logger: Logger instance
        dry_run: Whether to run in dry-run mode
        verbosity: Verbosity level
    """

    project_root: Path
    config: DevflowConfig
    logger: DevflowLogger
    dry_run: bool = False
    verbosity: int = 0

    @classmethod
    def create(
        cls,
        project_root: Optional[Path] = None,
        config_path: Optional[Path] = None,
        dry_run: bool = False,
        verbosity: int = 0,
        quiet: bool = False,
    ) -> "AppContext":
        """
        Create an AppContext instance.

        Args:
            project_root: Explicit project root, or None to auto-detect
            config_path: Explicit config file path
            dry_run: Enable dry-run mode
            verbosity: Verbosity level (0=normal, 1=verbose, 2=debug)
            quiet: Enable quiet mode

        Returns:
            AppContext instance
        """
        # Find or use project root
        if project_root is None:
            project_root = find_project_root()
        else:
            project_root = project_root.resolve()

        # Load configuration
        config = load_config(project_root, config_path)

        # Create logger
        logger = DevflowLogger(verbosity=verbosity, quiet=quiet)

        return cls(
            project_root=project_root,
            config=config,
            logger=logger,
            dry_run=dry_run,
            verbosity=verbosity,
        )

    def get_venv_dir(self) -> Path:
        """Get the absolute path to the venv directory."""
        return self.project_root / self.config.venv_dir
