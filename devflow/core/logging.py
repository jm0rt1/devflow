"""Logging utilities for devflow."""

import logging
import sys


class DevflowLogger:
    """Logger with support for verbosity levels and dry-run mode."""

    def __init__(self, name: str = "devflow", verbosity: int = 0, quiet: bool = False):
        """
        Initialize the logger.

        Args:
            name: Logger name
            verbosity: Verbosity level (0=INFO, 1=DEBUG, 2+=more verbose)
            quiet: If True, suppress all output except errors
        """
        self.logger = logging.getLogger(name)
        self.verbosity = verbosity
        self.quiet = quiet
        self._configure()

    def _configure(self) -> None:
        """Configure logging based on verbosity."""
        # Clear existing handlers
        self.logger.handlers.clear()

        # Create console handler
        handler = logging.StreamHandler(sys.stderr)

        # Set format
        if self.verbosity >= 2:
            fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        elif self.verbosity >= 1:
            fmt = "[%(levelname)s] %(message)s"
        else:
            fmt = "%(message)s"

        handler.setFormatter(logging.Formatter(fmt))
        self.logger.addHandler(handler)

        # Set level based on quiet/verbosity
        if self.quiet:
            self.logger.setLevel(logging.ERROR)
        elif self.verbosity >= 2:
            self.logger.setLevel(logging.DEBUG)
        elif self.verbosity >= 1:
            self.logger.setLevel(logging.DEBUG)
        else:
            self.logger.setLevel(logging.INFO)

    def debug(self, msg: str, *args, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args, **kwargs) -> None:
        """Log info message."""
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs) -> None:
        """Log error message."""
        self.logger.error(msg, *args, **kwargs)

    def phase(self, phase_name: str, msg: str) -> None:
        """Log a message with phase prefix."""
        self.info(f"[{phase_name}] {msg}")


def setup_logger(
    verbosity: int = 0, quiet: bool = False, name: str = "devflow"
) -> DevflowLogger:
    """
    Set up and return a configured logger.

    Args:
        verbosity: Verbosity level
        quiet: Quiet mode flag
        name: Logger name

    Returns:
        Configured DevflowLogger instance
    """
    return DevflowLogger(name=name, verbosity=verbosity, quiet=quiet)
