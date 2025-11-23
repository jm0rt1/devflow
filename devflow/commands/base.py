"""Base classes for devflow commands."""

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from devflow.app import AppContext


class Command(ABC):
    """Base class for all devflow commands."""

    name: str = ""
    help: str = ""

    def __init__(self, app: AppContext):
        """
        Initialize the command.

        Args:
            app: Application context
        """
        self.app = app

    @abstractmethod
    def run(self, **kwargs: Any) -> int:
        """
        Run the command.

        Args:
            **kwargs: Command-specific arguments

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


@dataclass
class Task:
    """Representation of a single executable task."""

    name: str
    command: List[str]
    use_venv: bool = True
    env: Optional[Dict[str, str]] = None
    cwd: Optional[Path] = None


class TaskExecutor:
    """Executor for running tasks with dry-run and logging support."""

    def __init__(self, app: AppContext):
        """
        Initialize the task executor.

        Args:
            app: Application context
        """
        self.app = app

    def execute_task(self, task: Task) -> int:
        """
        Execute a single task.

        Args:
            task: Task to execute

        Returns:
            Exit code from the task
        """
        # Build command
        cmd = task.command.copy()

        # Prepare environment
        env = task.env.copy() if task.env else {}

        # Log the command
        cmd_str = " ".join(cmd)
        self.app.logger.info(f"Running: {cmd_str}", prefix=task.name)

        if self.app.dry_run:
            self.app.logger.info("(dry-run, not actually executing)", prefix=task.name)
            return 0

        # Execute
        try:
            result = subprocess.run(
                cmd,
                cwd=task.cwd or self.app.project_root,
                env={**subprocess.os.environ, **env} if env else None,
                capture_output=self.app.verbosity < 2,
                text=True,
                shell=False,
            )

            if result.returncode != 0:
                self.app.logger.error(
                    f"Command failed with exit code {result.returncode}",
                    prefix=task.name,
                )
                if result.stderr and self.app.verbosity < 2:
                    self.app.logger.error(result.stderr, prefix=task.name)

            return result.returncode
        except FileNotFoundError as e:
            self.app.logger.error(f"Command not found: {e}", prefix=task.name)
            return 127
        except Exception as e:
            self.app.logger.error(f"Error executing command: {e}", prefix=task.name)
            return 1

    def execute_pipeline(self, tasks: List[Task]) -> int:
        """
        Execute a pipeline of tasks in sequence.

        Args:
            tasks: List of tasks to execute

        Returns:
            Exit code (first non-zero exit code, or 0 if all succeed)
        """
        for task in tasks:
            exit_code = self.execute_task(task)
            if exit_code != 0:
                return exit_code
        return 0
