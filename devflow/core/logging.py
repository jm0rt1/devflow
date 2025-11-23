"""Structured logging for devflow with verbosity support."""

import logging
import sys
from typing import Optional


class DevflowLogger:
    """Logger with phase prefixes and verbosity control."""

    def __init__(self, verbosity: int = 0, quiet: bool = False):
        self.verbosity = verbosity
        self.quiet = quiet
        self._setup_logger()

    def _setup_logger(self) -> None:
        """Set up the logger with appropriate level."""
        self.logger = logging.getLogger("devflow")
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set level based on verbosity
        if self.quiet:
            level = logging.ERROR
        elif self.verbosity >= 2:
            level = logging.DEBUG
        elif self.verbosity >= 1:
            level = logging.INFO
        else:
            level = logging.WARNING
        
        self.logger.setLevel(level)
        
        # Console handler with formatting
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

    def info(self, message: str, phase: Optional[str] = None) -> None:
        """Log info message with optional phase prefix."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.info(message)

    def debug(self, message: str, phase: Optional[str] = None) -> None:
        """Log debug message with optional phase prefix."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.debug(message)

    def warning(self, message: str, phase: Optional[str] = None) -> None:
        """Log warning message with optional phase prefix."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.warning(message)

    def error(self, message: str, phase: Optional[str] = None) -> None:
        """Log error message with optional phase prefix."""
        if phase:
            message = f"[{phase}] {message}"
        self.logger.error(message)

    def dry_run(self, message: str, phase: Optional[str] = None) -> None:
        """Log dry-run action."""
        prefix = "[DRY-RUN]"
        if phase:
            prefix = f"[DRY-RUN][{phase}]"
        self.logger.info(f"{prefix} {message}")
