"""Task and Pipeline abstractions for devflow.

This module defines the core task execution model for devflow. Tasks represent
single operations (e.g., run pytest, build package) while Pipelines represent
sequences of tasks that run in order.

Ownership: Workstream B (task/registry)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Union


@dataclass
class Task:
    """A single executable task in devflow.

    Tasks represent atomic operations like running a command or script.
    They support venv-aware execution, environment variable overrides,
    and configurable argument lists.

    Attributes:
        name: Unique identifier for the task.
        command: The executable command (e.g., 'pytest', 'python').
        args: List of arguments to pass to the command.
        use_venv: Whether to execute the command within the project venv.
        env: Environment variable overrides for the command.
        working_dir: Optional working directory (relative to project root).

    Example:
        >>> task = Task(
        ...     name="test",
        ...     command="pytest",
        ...     args=["-q", "--tb=short"],
        ...     use_venv=True,
        ...     env={"PYTHONDONTWRITEBYTECODE": "1"}
        ... )
    """

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    use_venv: bool = True
    env: dict[str, str] | None = None
    working_dir: str | None = None

    def to_command_list(self) -> list[str]:
        """Convert task to a command list suitable for subprocess.

        Returns:
            List containing the command and its arguments.
        """
        return [self.command, *self.args]


@dataclass
class Pipeline:
    """A sequence of tasks that execute in order.

    Pipelines provide composite task execution with short-circuit behavior
    on failure. If any task in the pipeline fails (non-zero exit code),
    subsequent tasks are not executed.

    Attributes:
        name: Unique identifier for the pipeline.
        steps: List of task names (strings) or Task objects that make up the pipeline.

    Example:
        >>> pipeline = Pipeline(
        ...     name="ci-check",
        ...     steps=["format", "lint", "test"]
        ... )
    """

    name: str
    steps: list[str | Task] = field(default_factory=list)


# Type alias for task definitions that can be either a Task or Pipeline
TaskDefinition = Union[Task, Pipeline]


def is_pipeline(task_def: TaskDefinition) -> bool:
    """Check if a task definition is a Pipeline.

    Args:
        task_def: A Task or Pipeline instance.

    Returns:
        True if the definition is a Pipeline, False if it's a Task.
    """
    return isinstance(task_def, Pipeline)


def is_task(task_def: TaskDefinition) -> bool:
    """Check if a task definition is a Task.

    Args:
        task_def: A Task or Pipeline instance.

    Returns:
        True if the definition is a Task, False if it's a Pipeline.
    """
    return isinstance(task_def, Task)
