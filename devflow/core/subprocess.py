"""Subprocess utilities for devflow."""

import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from devflow.core.logging import DevFlowLogger


class SubprocessRunner:
    """
    Wrapper for running external commands with logging and dry-run support.
    """

    def __init__(
        self,
        logger: DevFlowLogger,
        dry_run: bool = False,
        cwd: Optional[Path] = None,
    ):
        """
        Initialize subprocess runner.

        Args:
            logger: Logger instance
            dry_run: If True, log commands but don't execute
            cwd: Working directory for commands
        """
        self.logger = logger
        self.dry_run = dry_run
        self.cwd = cwd

    def run(
        self,
        cmd: List[str],
        phase: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        check: bool = True,
        capture_output: bool = False,
    ) -> subprocess.CompletedProcess:
        """
        Run a command with logging.

        Args:
            cmd: Command and arguments as list
            phase: Optional phase name for logging
            env: Optional environment variables
            check: If True, raise on non-zero exit code
            capture_output: If True, capture stdout/stderr

        Returns:
            CompletedProcess instance

        Raises:
            subprocess.CalledProcessError: If check=True and command fails
        """
        self.logger.command(cmd, phase=phase)

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would execute: {' '.join(str(c) for c in cmd)}", phase=phase)
            # Return a fake successful result
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout=b"" if capture_output else None,
                stderr=b"" if capture_output else None,
            )

        try:
            result = subprocess.run(
                cmd,
                cwd=self.cwd,
                env=env,
                check=check,
                capture_output=capture_output,
                shell=False,  # Always use explicit arg lists
            )
            return result
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Command failed with exit code {e.returncode}", phase=phase)
            raise
