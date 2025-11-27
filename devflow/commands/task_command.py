"""Task command for running custom tasks from config.

This module provides the `devflow task <name>` CLI command that executes
tasks defined in the project configuration.

Ownership: Workstream B (task/registry)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from devflow.commands.base import Command
from devflow.commands.executor import (
    CycleDetectedError,
    ExecutionResult,
    PipelineResult,
    TaskExecutor,
    TaskNotFoundError,
    create_executor_from_config,
)

if TYPE_CHECKING:
    from typing import Protocol

    class AppContext(Protocol):
        """Protocol for AppContext (owned by Workstream A)."""

        project_root: Path
        config: Any
        dry_run: bool
        verbosity: int


class TaskCommand(Command):
    """Command to run custom tasks defined in configuration.

    This command allows users to run tasks defined in the [tool.devflow.tasks]
    section of their configuration file.

    Example:
        >>> # In pyproject.toml:
        >>> # [tool.devflow.tasks.lint]
        >>> # command = "ruff"
        >>> # args = ["check", "."]
        >>>
        >>> # Command line:
        >>> # devflow task lint
    """

    name = "task"
    help = "Run a custom task defined in project configuration"

    def __init__(self, app: AppContext) -> None:
        """Initialize the task command.

        Args:
            app: Application context with config and settings.
        """
        super().__init__(app)
        self._executor: TaskExecutor | None = None

    def _get_executor(self) -> TaskExecutor:
        """Get or create the task executor.

        Returns:
            Configured TaskExecutor instance.
        """
        if self._executor is None:
            # Get tasks config - Workstream A provides the config structure
            config = getattr(self.app.config, "to_dict", lambda: self.app.config)()
            if isinstance(config, dict):
                tasks_config = config
            else:
                # Handle case where config might be a dataclass/pydantic model
                tasks_config = {"tasks": getattr(self.app.config, "tasks", {})}

            # Get venv path if configured
            venv_path = None
            if hasattr(self.app.config, "venv_dir"):
                venv_dir = getattr(self.app.config, "venv_dir", ".venv")
                venv_path = self.app.project_root / venv_dir

            self._executor = create_executor_from_config(
                config=tasks_config,
                project_root=self.app.project_root,
                dry_run=self.app.dry_run,
                verbosity=self.app.verbosity,
                venv_path=venv_path,
            )

        return self._executor

    def list_tasks(self) -> list[str]:
        """List all available task names.

        Returns:
            Sorted list of task names from configuration.
        """
        executor = self._get_executor()
        return sorted(executor.task_definitions.keys())

    def run(self, task_name: str | None = None, list_tasks: bool = False, **kwargs: Any) -> int:
        """Execute a task by name.

        Args:
            task_name: Name of the task to run.
            list_tasks: If True, list available tasks and exit.
            **kwargs: Additional arguments (unused).

        Returns:
            Exit code: 0 for success, non-zero for failure.
        """
        if list_tasks or task_name is None:
            return self._list_available_tasks()

        executor = self._get_executor()

        try:
            result = executor.run(task_name)
        except TaskNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("\nTo see available tasks, run: devflow task --list", file=sys.stderr)
            return 1
        except CycleDetectedError as e:
            print(f"Error: {e}", file=sys.stderr)
            print("\nFix the cycle in your task definitions.", file=sys.stderr)
            return 1

        if isinstance(result, PipelineResult):
            return result.exit_code
        elif isinstance(result, ExecutionResult):
            return result.exit_code
        else:
            return 0

    def _list_available_tasks(self) -> int:
        """List all available tasks.

        Returns:
            Exit code 0.
        """
        tasks = self.list_tasks()
        if not tasks:
            print("No tasks defined in configuration.", file=sys.stderr)
            print(
                "\nDefine tasks in [tool.devflow.tasks] section of your pyproject.toml.",
                file=sys.stderr,
            )
            return 0

        print("Available tasks:")
        for task_name in tasks:
            print(f"  - {task_name}")
        return 0


def create_task_typer_command(app_context: Any) -> Any:
    """Create a Typer command function for the task command.

    This function creates a callback suitable for use with Typer that
    wraps the TaskCommand class.

    Args:
        app_context: The application context.

    Returns:
        A function that can be used as a Typer command callback.

    Example:
        >>> import typer
        >>> app = typer.Typer()
        >>> task_cmd = create_task_typer_command(app_context)
        >>> app.command("task")(task_cmd)
    """

    def task_callback(
        task_name: str | None = None,
        list_tasks: bool = False,
    ) -> None:
        """Run a custom task defined in project configuration.

        Args:
            task_name: Name of the task to run.
            list_tasks: List available tasks and exit.
        """
        cmd = TaskCommand(app_context)
        exit_code = cmd.run(task_name=task_name, list_tasks=list_tasks)
        if exit_code != 0:
            raise SystemExit(exit_code)

    return task_callback
