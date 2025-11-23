"""Structured logging utilities."""

import sys
from enum import IntEnum


class LogLevel(IntEnum):
    """Logging verbosity levels."""

    QUIET = 0
    NORMAL = 1
    VERBOSE = 2
    DEBUG = 3


class Logger:
    """Structured logger with verbosity control."""

    def __init__(self, level: LogLevel = LogLevel.NORMAL):
        """Initialize logger with verbosity level."""
        self.level = level

    def _log(self, msg: str, prefix: str = "", level: LogLevel = LogLevel.NORMAL) -> None:
        """Internal logging method."""
        if self.level >= level:
            if prefix:
                print(f"{prefix} {msg}", file=sys.stderr)
            else:
                print(msg, file=sys.stderr)

    def info(self, msg: str, prefix: str = "") -> None:
        """Log informational message."""
        self._log(msg, prefix, LogLevel.NORMAL)

    def verbose(self, msg: str, prefix: str = "") -> None:
        """Log verbose message."""
        self._log(msg, prefix, LogLevel.VERBOSE)

    def debug(self, msg: str, prefix: str = "") -> None:
        """Log debug message."""
        self._log(msg, prefix, LogLevel.DEBUG)

    def error(self, msg: str, prefix: str = "") -> None:
        """Log error message."""
        # Errors always show regardless of level
        print(f"ERROR: {prefix} {msg}" if prefix else f"ERROR: {msg}", file=sys.stderr)

    def warning(self, msg: str, prefix: str = "") -> None:
        """Log warning message."""
        if self.level >= LogLevel.NORMAL:
            print(f"WARNING: {prefix} {msg}" if prefix else f"WARNING: {msg}", file=sys.stderr)
