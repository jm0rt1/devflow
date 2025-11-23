"""Base command and task abstractions."""

import subprocess
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from devflow.app import AppContext


class Command(ABC):
    """Base class for all commands."""

    name: str
    help: str

    def __init__(self, app: "AppContext"):
        """Initialize command with app context."""
        self.app = app

    @abstractmethod
    def run(self, **kwargs) -> int:
        """
        Execute the command.

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        pass


class CommandRegistry:
    """Registry for available commands."""

    def __init__(self):
        """Initialize empty registry."""
        self._commands: dict[str, type[Command]] = {}

    def register(self, cmd_cls: type[Command]) -> None:
        """Register a command class."""
        self._commands[cmd_cls.name] = cmd_cls

    def get(self, name: str) -> type[Command] | None:
        """Get a command class by name."""
        return self._commands.get(name)

    def list_commands(self) -> list[str]:
        """List all registered command names."""
        return sorted(self._commands.keys())


@dataclass
class Task:
    """
    Represents a single executable task.

    A task is a command with arguments, environment variables,
    and configuration for how it should be executed.
    """

    name: str
    command: list[str]  # Command and arguments as a list
    use_venv: bool = True
    env: dict[str, str] = field(default_factory=dict)
    cwd: Path | None = None

    def execute(self, app: "AppContext") -> int:
        """
        Execute the task.

        Args:
            app: Application context for logging and configuration

        Returns:
            Exit code from the command
        """
        # Log what we're doing
        cmd_str = " ".join(self.command)
        prefix = f"[{self.name}]"

        if app.dry_run:
            app.logger.info(f"Would execute: {cmd_str}", prefix=prefix)
            if self.env:
                app.logger.verbose(f"Environment: {self.env}", prefix=prefix)
            return 0

        app.logger.info(f"Executing: {cmd_str}", prefix=prefix)
        app.logger.verbose(f"Working directory: {self.cwd or app.project_root}", prefix=prefix)

        # Prepare environment
        import os
        env = os.environ.copy()
        env.update(self.env)

        # Add venv to PATH if requested
        if self.use_venv:
            import sys
            # Use 'Scripts' on Windows, 'bin' on Unix-like systems
            venv_bin_dir = "Scripts" if sys.platform == "win32" else "bin"
            venv_bin = app.venv_path / venv_bin_dir
            if venv_bin.exists():
                # Use appropriate path separator for platform
                path_sep = ";" if sys.platform == "win32" else ":"
                env["PATH"] = f"{venv_bin}{path_sep}{env.get('PATH', '')}"
                env["VIRTUAL_ENV"] = str(app.venv_path)
                app.logger.debug(f"Using venv: {app.venv_path}", prefix=prefix)
            else:
                app.logger.warning(
                    f"Venv not found at {app.venv_path}, executing without venv",
                    prefix=prefix
                )

        # Execute command
        try:
            result = subprocess.run(
                self.command,
                cwd=self.cwd or app.project_root,
                env=env,
                shell=False,  # Always use shell=False for security
            )

            if result.returncode != 0:
                app.logger.error(
                    f"Command failed with exit code {result.returncode}",
                    prefix=prefix
                )
            else:
                app.logger.verbose("Command succeeded", prefix=prefix)

            return result.returncode

        except FileNotFoundError:
            app.logger.error(f"Command not found: {self.command[0]}", prefix=prefix)
            return 127
        except Exception as e:
            app.logger.error(f"Execution failed: {e}", prefix=prefix)
            return 1


@dataclass
class Pipeline:
    """
    Represents a pipeline of tasks to be executed in sequence.

    Pipeline execution stops at the first failure (non-zero exit code).
    """

    name: str
    tasks: list[Task] = field(default_factory=list)

    def execute(self, app: "AppContext") -> int:
        """
        Execute all tasks in the pipeline.

        Tasks are executed in order. If any task fails (non-zero exit code),
        execution stops and the exit code is returned.

        Args:
            app: Application context for logging and configuration

        Returns:
            Exit code (0 if all tasks succeed, or first non-zero exit code)
        """
        prefix = f"[{self.name}]"
        app.logger.info(f"Starting pipeline with {len(self.tasks)} task(s)", prefix=prefix)

        for i, task in enumerate(self.tasks, 1):
            app.logger.verbose(f"Task {i}/{len(self.tasks)}: {task.name}", prefix=prefix)

            exit_code = task.execute(app)

            if exit_code != 0:
                app.logger.error(
                    f"Pipeline failed at task '{task.name}' with exit code {exit_code}",
                    prefix=prefix
                )
                return exit_code

        app.logger.info("Pipeline completed successfully", prefix=prefix)
        return 0
