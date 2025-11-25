# devflow.commands - Command Framework & Task Engine
"""Command framework and task engine for devflow."""

from devflow.commands.base import Command, CommandRegistry
from devflow.commands.task import Task, Pipeline, TaskDefinition, is_pipeline, is_task
from devflow.commands.executor import (
    TaskExecutor,
    ExecutionResult,
    PipelineResult,
    CycleDetectedError,
    TaskNotFoundError,
    create_executor_from_config,
)
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
