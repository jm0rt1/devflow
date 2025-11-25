"""Task execution engine for devflow.

This module provides the TaskExecutor class that handles running tasks
and pipelines with proper logging, dry-run support, environment propagation,
and exit code handling.

Ownership: Workstream B (task/registry)
"""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from devflow.commands.task import Pipeline, Task, TaskDefinition, is_pipeline

if TYPE_CHECKING:
    from typing import Protocol

    class AppContext(Protocol):
        """Protocol for AppContext (owned by Workstream A)."""

        project_root: Path
        config: Any
        dry_run: bool
        verbosity: int


@dataclass
class ExecutionResult:
    """Result of a task execution.

    Attributes:
        task_name: Name of the task that was executed.
        exit_code: Exit code from the task (0 = success).
        output: Captured stdout/stderr if available.
        skipped: Whether the task was skipped (dry-run mode).
        error: Error message if the task failed to start.
    """

    task_name: str
    exit_code: int
    output: str = ""
    skipped: bool = False
    error: str | None = None


@dataclass
class PipelineResult:
    """Result of a pipeline execution.

    Attributes:
        pipeline_name: Name of the pipeline.
        results: List of ExecutionResults for each task in the pipeline.
        short_circuited: Whether the pipeline was short-circuited due to failure.
    """

    pipeline_name: str
    results: list[ExecutionResult] = field(default_factory=list)
    short_circuited: bool = False

    @property
    def exit_code(self) -> int:
        """Get the final exit code of the pipeline.

        Returns:
            0 if all tasks succeeded, otherwise the exit code of the first failure.
        """
        for result in self.results:
            if result.exit_code != 0:
                return result.exit_code
        return 0

    @property
    def success(self) -> bool:
        """Check if the pipeline completed successfully."""
        return self.exit_code == 0


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in pipeline expansion."""

    def __init__(self, cycle_path: list[str]) -> None:
        """Initialize with the cycle path.

        Args:
            cycle_path: List of task names forming the cycle.
        """
        self.cycle_path = cycle_path
        cycle_str = " -> ".join(cycle_path)
        super().__init__(f"Cycle detected in pipeline: {cycle_str}")


class TaskNotFoundError(Exception):
    """Raised when a referenced task is not found."""

    def __init__(self, task_name: str, available_tasks: list[str] | None = None) -> None:
        """Initialize with the missing task name.

        Args:
            task_name: Name of the task that was not found.
            available_tasks: List of available task names for the error message.
        """
        self.task_name = task_name
        self.available_tasks = available_tasks or []
        msg = f"Task '{task_name}' not found"
        if self.available_tasks:
            msg += f". Available tasks: {', '.join(sorted(self.available_tasks))}"
        super().__init__(msg)


# Type for the logging callback function
LogCallback = Callable[[str, str, int], None]


class TaskExecutor:
    """Executor for running tasks and pipelines.

    The TaskExecutor handles all aspects of task execution:
    - Dry-run mode (logging commands without executing)
    - Verbosity levels for logging
    - Environment variable propagation
    - Exit code handling with short-circuit behavior
    - Pipeline expansion with cycle detection

    Attributes:
        task_definitions: Dictionary mapping task names to their definitions.
        project_root: Path to the project root directory.
        dry_run: Whether to run in dry-run mode.
        verbosity: Logging verbosity level (-1=quiet, 0=normal, 1+=verbose).
        log_callback: Optional callback for custom logging.
    """

    def __init__(
        self,
        task_definitions: dict[str, TaskDefinition],
        project_root: Path | None = None,
        dry_run: bool = False,
        verbosity: int = 0,
        log_callback: LogCallback | None = None,
        venv_path: Path | None = None,
    ) -> None:
        """Initialize the task executor.

        Args:
            task_definitions: Dictionary mapping task names to Task/Pipeline objects.
            project_root: Project root directory (defaults to cwd).
            dry_run: Whether to run in dry-run mode.
            verbosity: Logging verbosity (-1=quiet, 0=normal, 1+=verbose).
            log_callback: Optional callback for custom logging (phase, message, level).
            venv_path: Path to the virtual environment (for use_venv tasks).
        """
        self.task_definitions = task_definitions
        self.project_root = project_root or Path.cwd()
        self.dry_run = dry_run
        self.verbosity = verbosity
        self.log_callback = log_callback
        self.venv_path = venv_path

    def _log(self, phase: str, message: str, level: int = 0) -> None:
        """Log a message with a phase prefix.

        Args:
            phase: The phase/task name (e.g., 'test', 'build').
            message: The message to log.
            level: Verbosity level required to show this message.
                   -1 = always show (except in quiet mode)
                    0 = show at default verbosity
                    1+ = show only with increased verbosity
        """
        if self.verbosity < level:
            return

        if self.log_callback:
            self.log_callback(phase, message, level)
        else:
            # Default logging to stderr
            prefix = f"[{phase}]" if phase else ""
            print(f"{prefix} {message}", file=sys.stderr)

    def expand_pipeline(
        self, name: str, visited: set[str] | None = None, path: list[str] | None = None
    ) -> list[Task]:
        """Recursively expand a pipeline into a flat list of tasks.

        This method handles nested pipelines and detects cycles to prevent
        infinite recursion.

        Args:
            name: Name of the task/pipeline to expand.
            visited: Set of task names that have been fully processed.
            path: Current path in the expansion (for cycle detection).

        Returns:
            List of Task objects in execution order.

        Raises:
            TaskNotFoundError: If a referenced task is not found.
            CycleDetectedError: If a cycle is detected in the pipeline.
        """
        if visited is None:
            visited = set()
        if path is None:
            path = []

        # Check for cycles
        if name in path:
            raise CycleDetectedError(path + [name])

        # Get the task definition
        task_def = self.task_definitions.get(name)
        if task_def is None:
            raise TaskNotFoundError(name, list(self.task_definitions.keys()))

        # If it's a simple task, return it
        if not is_pipeline(task_def):
            return [task_def]  # type: ignore[list-item]

        # It's a pipeline - expand it
        pipeline: Pipeline = task_def  # type: ignore[assignment]
        expanded: list[Task] = []
        new_path = path + [name]

        for step in pipeline.steps:
            if isinstance(step, str):
                # It's a reference to another task/pipeline
                expanded.extend(self.expand_pipeline(step, visited, new_path))
            else:
                # It's an inline Task
                expanded.append(step)

        visited.add(name)
        return expanded

    def _build_env(self, task: Task) -> dict[str, str]:
        """Build the environment for a task execution.

        Combines the current environment with task-specific overrides.

        Args:
            task: The task to build the environment for.

        Returns:
            Environment dictionary for subprocess execution.
        """
        env = os.environ.copy()

        # Apply task-specific environment overrides
        if task.env:
            env.update(task.env)

        return env

    def _get_executable_path(self, task: Task) -> str:
        """Get the executable path for a task.

        If use_venv is True and a venv_path is configured, returns the
        path to the executable within the venv.

        Args:
            task: The task to get the executable for.

        Returns:
            Path to the executable.
        """
        command = task.command

        if task.use_venv and self.venv_path:
            # Try to find the command in the venv
            if sys.platform == "win32":
                venv_bin = self.venv_path / "Scripts"
            else:
                venv_bin = self.venv_path / "bin"

            # Check for the command in venv
            venv_cmd = venv_bin / command
            if venv_cmd.exists():
                return str(venv_cmd)

            # For python, try to use the venv python
            if command in ("python", "python3"):
                if sys.platform == "win32":
                    venv_python = venv_bin / "python.exe"
                else:
                    venv_python = venv_bin / "python"
                if venv_python.exists():
                    return str(venv_python)

        return command

    def execute_task(self, task: Task) -> ExecutionResult:
        """Execute a single task.

        Args:
            task: The task to execute.

        Returns:
            ExecutionResult with exit code and output.
        """
        executable = self._get_executable_path(task)
        command_list = [executable, *task.args]
        env = self._build_env(task)

        # Determine working directory
        working_dir = self.project_root
        if task.working_dir:
            working_dir = self.project_root / task.working_dir

        # Log the command
        cmd_str = " ".join(command_list)
        if self.dry_run:
            self._log(task.name, f"Would run: {cmd_str}", level=0)
            return ExecutionResult(
                task_name=task.name,
                exit_code=0,
                skipped=True,
            )

        self._log(task.name, f"Running: {cmd_str}", level=1)

        try:
            # Execute the command with explicit arg list (shell=False)
            result = subprocess.run(
                command_list,
                cwd=working_dir,
                env=env,
                capture_output=self.verbosity < 1,  # Capture output only in non-verbose mode
                text=True,
            )

            output = ""
            if result.stdout:
                output += result.stdout
            if result.stderr:
                output += result.stderr

            if result.returncode != 0:
                self._log(task.name, f"Failed with exit code {result.returncode}", level=-1)

            return ExecutionResult(
                task_name=task.name,
                exit_code=result.returncode,
                output=output,
            )

        except FileNotFoundError:
            error_msg = f"Command not found: {executable}"
            self._log(task.name, error_msg, level=-1)
            return ExecutionResult(
                task_name=task.name,
                exit_code=127,  # Standard "command not found" exit code
                error=error_msg,
            )
        except PermissionError:
            error_msg = f"Permission denied: {executable}"
            self._log(task.name, error_msg, level=-1)
            return ExecutionResult(
                task_name=task.name,
                exit_code=126,  # Standard "permission denied" exit code
                error=error_msg,
            )
        except Exception as e:
            error_msg = f"Error executing task: {e}"
            self._log(task.name, error_msg, level=-1)
            return ExecutionResult(
                task_name=task.name,
                exit_code=1,
                error=error_msg,
            )

    def run(self, task_name: str) -> ExecutionResult | PipelineResult:
        """Run a task or pipeline by name.

        If the task is a pipeline, it expands and executes all steps in order,
        short-circuiting on the first failure.

        Args:
            task_name: Name of the task or pipeline to run.

        Returns:
            ExecutionResult for a single task, PipelineResult for a pipeline.

        Raises:
            TaskNotFoundError: If the task is not found.
            CycleDetectedError: If a cycle is detected in pipeline expansion.
        """
        task_def = self.task_definitions.get(task_name)
        if task_def is None:
            raise TaskNotFoundError(task_name, list(self.task_definitions.keys()))

        # If it's a simple task, execute it directly
        if not is_pipeline(task_def):
            task: Task = task_def  # type: ignore[assignment]
            self._log(task.name, "Starting task", level=0)
            result = self.execute_task(task)
            if result.exit_code == 0:
                self._log(task.name, "Completed successfully", level=0)
            return result

        # It's a pipeline - expand and execute
        self._log(task_name, "Starting pipeline", level=0)

        try:
            tasks = self.expand_pipeline(task_name)
        except CycleDetectedError:
            raise
        except TaskNotFoundError:
            raise

        pipeline_result = PipelineResult(pipeline_name=task_name)

        for task in tasks:
            self._log(task_name, f"Running step: {task.name}", level=0)
            result = self.execute_task(task)
            pipeline_result.results.append(result)

            # Short-circuit on failure
            if result.exit_code != 0:
                self._log(
                    task_name,
                    f"Pipeline short-circuited at '{task.name}' with exit code {result.exit_code}",
                    level=-1,
                )
                pipeline_result.short_circuited = True
                break

        if pipeline_result.success:
            self._log(task_name, "Pipeline completed successfully", level=0)

        return pipeline_result


def create_executor_from_config(
    config: dict[str, Any],
    project_root: Path | None = None,
    dry_run: bool = False,
    verbosity: int = 0,
    venv_path: Path | None = None,
) -> TaskExecutor:
    """Create a TaskExecutor from a configuration dictionary.

    This helper function parses task definitions from a config dictionary
    (typically loaded from pyproject.toml or devflow.toml) and creates
    an executor.

    Args:
        config: Configuration dictionary with a 'tasks' key.
        project_root: Project root directory.
        dry_run: Whether to run in dry-run mode.
        verbosity: Logging verbosity level.
        venv_path: Path to the virtual environment.

    Returns:
        Configured TaskExecutor instance.

    Example:
        >>> config = {
        ...     'tasks': {
        ...         'test': {'command': 'pytest', 'args': ['-q']},
        ...         'ci-check': {'pipeline': ['lint', 'test']}
        ...     }
        ... }
        >>> executor = create_executor_from_config(config)
    """
    task_definitions: dict[str, TaskDefinition] = {}

    tasks_config = config.get("tasks", {})

    for name, task_config in tasks_config.items():
        if "pipeline" in task_config:
            # It's a pipeline
            task_definitions[name] = Pipeline(
                name=name,
                steps=task_config["pipeline"],
            )
        else:
            # It's a task
            task_definitions[name] = Task(
                name=name,
                command=task_config.get("command", ""),
                args=task_config.get("args", []),
                use_venv=task_config.get("use_venv", True),
                env=task_config.get("env"),
                working_dir=task_config.get("working_dir"),
            )

    return TaskExecutor(
        task_definitions=task_definitions,
        project_root=project_root,
        dry_run=dry_run,
        verbosity=verbosity,
        venv_path=venv_path,
    )
