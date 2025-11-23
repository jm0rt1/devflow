"""Custom task execution with pipeline expansion and cycle detection."""

from typing import TYPE_CHECKING

from devflow.config import TaskConfig

from .base import Command, Pipeline, Task

if TYPE_CHECKING:
    pass


class CycleError(Exception):
    """Raised when a cycle is detected in task dependencies."""

    pass


class TaskNotFoundError(Exception):
    """Raised when a task is not found in configuration."""

    pass


def expand_pipeline(
    task_name: str,
    tasks_config: dict[str, TaskConfig],
    visited: set[str] | None = None,
    path: list[str] | None = None,
) -> list[Task]:
    """
    Expand a task into a list of Task objects, handling pipelines recursively.

    Detects cycles and provides clear error messages.

    Args:
        task_name: Name of the task to expand
        tasks_config: Dictionary of task configurations
        visited: Set of tasks currently being expanded (for cycle detection)
        path: Current expansion path (for error messages)

    Returns:
        List of Task objects in execution order

    Raises:
        TaskNotFoundError: If task is not found in configuration
        CycleError: If a cycle is detected in task dependencies
    """
    if visited is None:
        visited = set()
    if path is None:
        path = []

    # Check if task exists
    if task_name not in tasks_config:
        raise TaskNotFoundError(
            f"Task '{task_name}' not found. Available tasks: {', '.join(sorted(tasks_config.keys()))}"
        )

    # Check for cycle
    if task_name in visited:
        cycle_path = " -> ".join(path + [task_name])
        raise CycleError(f"Cycle detected in task dependencies: {cycle_path}")

    # Mark as visiting
    visited.add(task_name)
    path.append(task_name)

    task_config = tasks_config[task_name]
    result: list[Task] = []

    try:
        if task_config.is_pipeline():
            # Expand each task in the pipeline
            assert task_config.pipeline is not None
            for subtask_name in task_config.pipeline:
                subtasks = expand_pipeline(subtask_name, tasks_config, visited.copy(), path.copy())
                result.extend(subtasks)
        elif task_config.is_command():
            # Create a single task
            assert task_config.command is not None
            command = [task_config.command] + task_config.args
            result.append(
                Task(
                    name=task_name,
                    command=command,
                    use_venv=task_config.use_venv,
                    env=task_config.env,
                )
            )
        else:
            raise ValueError(
                f"Task '{task_name}' must specify either 'command' or 'pipeline'"
            )
    finally:
        # Clean up visiting state
        visited.discard(task_name)
        if path and path[-1] == task_name:
            path.pop()

    return result


class TaskCommand(Command):
    """Execute a custom task defined in configuration."""

    name = "task"
    help = "Run a custom task defined in configuration"

    def run(self, task_name: str) -> int:
        """
        Execute a custom task.

        Args:
            task_name: Name of the task to execute

        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        try:
            # Expand the task into a list of executable tasks
            tasks = expand_pipeline(task_name, self.app.config.tasks)

            if not tasks:
                self.app.logger.error(f"Task '{task_name}' expanded to no executable tasks")
                return 1

            # Create and execute pipeline
            if len(tasks) == 1:
                # Single task - execute directly
                return tasks[0].execute(self.app)
            else:
                # Multiple tasks - execute as pipeline
                pipeline = Pipeline(name=task_name, tasks=tasks)
                return pipeline.execute(self.app)

        except TaskNotFoundError as e:
            self.app.logger.error(str(e))
            return 1
        except CycleError as e:
            self.app.logger.error(str(e))
            return 1
        except Exception as e:
            self.app.logger.error(f"Failed to execute task '{task_name}': {e}")
            return 1
