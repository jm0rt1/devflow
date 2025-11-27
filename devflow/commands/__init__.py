"""Commands module for devflow.

This module provides command handlers for the CLI.
Actual command implementations are owned by their respective workstreams:
- Workstream B: Command base/registry and task engine
- Workstream C: venv and deps commands
- Workstream D: test, build, publish commands
- Workstream E: git commands
- Workstream F: plugin system
- Workstream G: completion and UX
"""

from devflow.commands.base import Command, CommandRegistry
from devflow.commands.executor import (
    CycleDetectedError,
    ExecutionResult,
    PipelineResult,
    TaskExecutor,
    TaskNotFoundError,
    create_executor_from_config,
)
from devflow.commands.task import Pipeline, Task, TaskDefinition, is_pipeline, is_task
from devflow.commands.task_command import TaskCommand, create_task_typer_command

__all__ = [
    # Base classes
    "Command",
    "CommandRegistry",
    # Task abstractions
    "Task",
    "Pipeline",
    "TaskDefinition",
    "is_pipeline",
    "is_task",
    # Executor
    "TaskExecutor",
    "ExecutionResult",
    "PipelineResult",
    "CycleDetectedError",
    "TaskNotFoundError",
    "create_executor_from_config",
    # Task command
    "TaskCommand",
    "create_task_typer_command",
]
