"""Logging utilities for devflow."""

import logging
import sys
from typing import Optional


class DevFlowLogger:
    """
    Structured logger for devflow with verbosity and phase support.
    """

    def __init__(self, verbosity: int = 0, quiet: bool = False):
        """
        Initialize logger.

        Args:
            verbosity: Verbosity level (0=INFO, 1+=DEBUG)
            quiet: If True, suppress most output
        """
        self.verbosity = verbosity
        self.quiet = quiet

        # Configure logging
        if quiet:
            level = logging.ERROR
        elif verbosity >= 1:
            level = logging.DEBUG
        else:
            level = logging.INFO

        logging.basicConfig(
            level=level,
            format="%(message)s",
            stream=sys.stdout,
        )
        self.logger = logging.getLogger("devflow")

    def info(self, message: str, phase: Optional[str] = None) -> None:
        """Log info message."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.info(message)

    def debug(self, message: str, phase: Optional[str] = None) -> None:
        """Log debug message."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.debug(message)

    def error(self, message: str, phase: Optional[str] = None) -> None:
        """Log error message."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.error(message)

    def warning(self, message: str, phase: Optional[str] = None) -> None:
        """Log warning message."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.warning(message)

    def command(self, cmd: list, phase: Optional[str] = None) -> None:
        """Log a command being executed."""
        cmd_str = " ".join(str(c) for c in cmd)
        self.debug(f"Running: {cmd_str}", phase=phase)
