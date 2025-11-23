"""Application context for devflow."""

from pathlib import Path
from typing import Optional

from devflow.config.loader import load_config
from devflow.config.schema import DevflowConfig
from devflow.core.logging import DevflowLogger
from devflow.core.paths import find_project_root


class AppContext:
    """Central application context holding configuration and runtime state."""

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
            project_root: Optional explicit project root path
            config_path: Optional explicit config file path
            verbosity: Verbosity level (0=warning, 1=info, 2+=debug)
            quiet: Suppress all but error messages
            dry_run: Enable dry-run mode (log actions without executing)
        """
        self.dry_run = dry_run
        self.logger = DevflowLogger(verbosity=verbosity, quiet=quiet)
        
        # Detect or use provided project root
        try:
            self.project_root = project_root or find_project_root()
            self.logger.debug(f"Project root: {self.project_root}")
        except RuntimeError as e:
            self.logger.error(str(e))
            self.project_root = Path.cwd()
        
        # Load configuration
        try:
            self.config = load_config(self.project_root, config_path)
            self.logger.debug("Configuration loaded successfully")
        except Exception as e:
            self.logger.warning(f"Failed to load config, using defaults: {e}")
            self.config = DevflowConfig()
