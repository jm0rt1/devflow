"""Structured logging utilities for devflow."""

import logging
import sys
from typing import Optional


class DevflowLogger:
    """
    Structured logger for devflow with support for verbosity levels and prefixes.
    """

    def __init__(self, verbosity: int = 0, quiet: bool = False):
        """
        Initialize the logger.

        Args:
            verbosity: Verbosity level (0=INFO, 1=DEBUG, 2+=more detailed)
            quiet: If True, suppress all output except errors
        """
        self.verbosity = verbosity
        self.quiet = quiet
        self._logger = logging.getLogger("devflow")

        # Configure handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        self._logger.handlers.clear()
        self._logger.addHandler(handler)

        # Set level based on verbosity
        if quiet:
            self._logger.setLevel(logging.ERROR)
        elif verbosity >= 2:
            self._logger.setLevel(logging.DEBUG)
        elif verbosity >= 1:
            self._logger.setLevel(logging.INFO)
        else:
            self._logger.setLevel(logging.INFO)

    def info(self, message: str, prefix: Optional[str] = None):
        """Log an info message."""
        if prefix:
            message = f"[{prefix}] {message}"
        self._logger.info(message)

    def debug(self, message: str, prefix: Optional[str] = None):
        """Log a debug message."""
        if prefix:
            message = f"[{prefix}] {message}"
        self._logger.debug(message)

    def error(self, message: str, prefix: Optional[str] = None):
        """Log an error message."""
        if prefix:
            message = f"[{prefix}] {message}"
        self._logger.error(message)

    def warning(self, message: str, prefix: Optional[str] = None):
        """Log a warning message."""
        if prefix:
            message = f"[{prefix}] {message}"
        self._logger.warning(message)
