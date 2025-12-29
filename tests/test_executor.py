"""Tests for TaskExecutor - pipeline expansion, dry-run, env propagation, exit codes.

Ownership: Workstream B (task/registry)
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devflow.commands.executor import (
    CycleDetectedError,
    ExecutionResult,
    PipelineResult,
    TaskExecutor,
    TaskNotFoundError,
    create_executor_from_config,
)
from devflow.commands.task import Pipeline, Task


class TestPipelineExpansion:
    """Tests for pipeline expansion and cycle detection."""

    def test_expand_single_task(self):
        """Expanding a single task returns a list with that task."""
        task = Task(name="test", command="pytest")
        executor = TaskExecutor(task_definitions={"test": task})

        expanded = executor.expand_pipeline("test")
        assert len(expanded) == 1
        assert expanded[0] == task

    def test_expand_simple_pipeline(self):
        """Expanding a simple pipeline returns tasks in order."""
        task1 = Task(name="lint", command="ruff")
        task2 = Task(name="test", command="pytest")
        task3 = Task(name="build", command="python", args=["-m", "build"])
        pipeline = Pipeline(name="ci", steps=["lint", "test", "build"])

        executor = TaskExecutor(
            task_definitions={"lint": task1, "test": task2, "build": task3, "ci": pipeline}
        )

        expanded = executor.expand_pipeline("ci")
        assert len(expanded) == 3
        assert expanded[0] == task1
        assert expanded[1] == task2
        assert expanded[2] == task3

    def test_expand_nested_pipeline(self):
        """Expanding nested pipelines works correctly."""
        task1 = Task(name="lint", command="ruff")
        task2 = Task(name="test", command="pytest")
        task3 = Task(name="build", command="python", args=["-m", "build"])

        # Inner pipeline: lint + test
        check_pipeline = Pipeline(name="check", steps=["lint", "test"])

        # Outer pipeline: check + build
        ci_pipeline = Pipeline(name="ci", steps=["check", "build"])

        executor = TaskExecutor(
            task_definitions={
                "lint": task1,
                "test": task2,
                "build": task3,
                "check": check_pipeline,
                "ci": ci_pipeline,
            }
        )

        expanded = executor.expand_pipeline("ci")
        assert len(expanded) == 3
        assert expanded[0] == task1
        assert expanded[1] == task2
        assert expanded[2] == task3

    def test_expand_with_inline_task(self):
        """Pipelines with inline Task objects expand correctly."""
        task1 = Task(name="lint", command="ruff")
        inline_task = Task(name="inline", command="echo", args=["hello"])
        pipeline = Pipeline(name="ci", steps=["lint", inline_task])

        executor = TaskExecutor(task_definitions={"lint": task1, "ci": pipeline})

        expanded = executor.expand_pipeline("ci")
        assert len(expanded) == 2
        assert expanded[0] == task1
        assert expanded[1] == inline_task

    def test_cycle_detection_simple(self):
        """Simple cycle (A -> A) is detected."""
        pipeline = Pipeline(name="loop", steps=["loop"])
        executor = TaskExecutor(task_definitions={"loop": pipeline})

        with pytest.raises(CycleDetectedError) as exc_info:
            executor.expand_pipeline("loop")

        assert "loop" in exc_info.value.cycle_path

    def test_cycle_detection_indirect(self):
        """Indirect cycles (A -> B -> A) are detected."""
        pipeline_a = Pipeline(name="a", steps=["b"])
        pipeline_b = Pipeline(name="b", steps=["a"])

        executor = TaskExecutor(task_definitions={"a": pipeline_a, "b": pipeline_b})

        with pytest.raises(CycleDetectedError) as exc_info:
            executor.expand_pipeline("a")

        assert "a" in exc_info.value.cycle_path
        assert "b" in exc_info.value.cycle_path

    def test_cycle_detection_longer_path(self):
        """Longer cycles (A -> B -> C -> A) are detected."""
        pipeline_a = Pipeline(name="a", steps=["b"])
        pipeline_b = Pipeline(name="b", steps=["c"])
        pipeline_c = Pipeline(name="c", steps=["a"])

        executor = TaskExecutor(
            task_definitions={"a": pipeline_a, "b": pipeline_b, "c": pipeline_c}
        )

        with pytest.raises(CycleDetectedError) as exc_info:
            executor.expand_pipeline("a")

        cycle_path = exc_info.value.cycle_path
        assert len(cycle_path) >= 3

    def test_task_not_found(self):
        """TaskNotFoundError is raised for missing tasks."""
        executor = TaskExecutor(task_definitions={})

        with pytest.raises(TaskNotFoundError) as exc_info:
            executor.expand_pipeline("missing")

        assert exc_info.value.task_name == "missing"

    def test_task_not_found_in_pipeline(self):
        """TaskNotFoundError is raised for missing tasks in pipelines."""
        pipeline = Pipeline(name="ci", steps=["lint", "missing_task"])
        task = Task(name="lint", command="ruff")

        executor = TaskExecutor(task_definitions={"ci": pipeline, "lint": task})

        with pytest.raises(TaskNotFoundError) as exc_info:
            executor.expand_pipeline("ci")

        assert exc_info.value.task_name == "missing_task"

    def test_task_not_found_includes_available(self):
        """TaskNotFoundError includes available task names."""
        task = Task(name="test", command="pytest")
        executor = TaskExecutor(task_definitions={"test": task})

        with pytest.raises(TaskNotFoundError) as exc_info:
            executor.expand_pipeline("missing")

        assert "test" in exc_info.value.available_tasks


class TestDryRunBehavior:
    """Tests for dry-run mode."""

    def test_dry_run_does_not_execute(self):
        """In dry-run mode, commands are not actually executed."""
        task = Task(name="test", command="echo", args=["hello"])
        executor = TaskExecutor(
            task_definitions={"test": task},
            dry_run=True,
        )

        # This should not actually run echo
        result = executor.execute_task(task)

        assert result.skipped is True
        assert result.exit_code == 0

    def test_dry_run_pipeline_all_skipped(self):
        """In dry-run mode, all pipeline steps are skipped."""
        task1 = Task(name="lint", command="ruff")
        task2 = Task(name="test", command="pytest")
        pipeline = Pipeline(name="ci", steps=["lint", "test"])

        executor = TaskExecutor(
            task_definitions={"lint": task1, "test": task2, "ci": pipeline},
            dry_run=True,
        )

        result = executor.run("ci")
        assert isinstance(result, PipelineResult)
        assert all(r.skipped for r in result.results)


class TestEnvPropagation:
    """Tests for environment variable propagation."""

    def test_env_includes_current_env(self):
        """Task environment includes current environment."""
        task = Task(name="test", command="echo")
        executor = TaskExecutor(task_definitions={"test": task})

        with patch.dict(os.environ, {"EXISTING_VAR": "value"}):
            env = executor._build_env(task)
            assert "EXISTING_VAR" in env
            assert env["EXISTING_VAR"] == "value"

    def test_task_env_overrides(self):
        """Task-specific env overrides current environment."""
        task = Task(
            name="test", command="echo", env={"MY_VAR": "task_value", "EXISTING_VAR": "overridden"}
        )
        executor = TaskExecutor(task_definitions={"test": task})

        with patch.dict(os.environ, {"EXISTING_VAR": "original"}):
            env = executor._build_env(task)
            assert env["MY_VAR"] == "task_value"
            assert env["EXISTING_VAR"] == "overridden"


class TestExitCodePropagation:
    """Tests for exit code propagation and short-circuiting."""

    @patch("subprocess.run")
    def test_success_exit_code(self, mock_run):
        """Successful tasks return exit code 0."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        task = Task(name="test", command="echo", args=["hello"])
        executor = TaskExecutor(task_definitions={"test": task}, dry_run=False)

        result = executor.execute_task(task)
        assert result.exit_code == 0

    @patch("subprocess.run")
    def test_failure_exit_code(self, mock_run):
        """Failed tasks propagate exit code."""
        mock_run.return_value = MagicMock(returncode=42, stdout="", stderr="error")

        task = Task(name="test", command="false")
        executor = TaskExecutor(task_definitions={"test": task}, dry_run=False)

        result = executor.execute_task(task)
        assert result.exit_code == 42

    @patch("subprocess.run")
    def test_pipeline_short_circuits_on_failure(self, mock_run):
        """Pipeline stops on first failure."""
        # First task succeeds, second fails
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout="", stderr=""),
            MagicMock(returncode=1, stdout="", stderr="error"),
        ]

        task1 = Task(name="first", command="true")
        task2 = Task(name="second", command="false")
        task3 = Task(name="third", command="true")
        pipeline = Pipeline(name="ci", steps=["first", "second", "third"])

        executor = TaskExecutor(
            task_definitions={"first": task1, "second": task2, "third": task3, "ci": pipeline},
            dry_run=False,
        )

        result = executor.run("ci")
        assert isinstance(result, PipelineResult)
        assert result.short_circuited is True
        assert len(result.results) == 2  # Third task not executed
        assert result.exit_code == 1

    @patch("subprocess.run")
    def test_pipeline_success_no_short_circuit(self, mock_run):
        """Successful pipeline runs all steps."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        task1 = Task(name="first", command="true")
        task2 = Task(name="second", command="true")
        task3 = Task(name="third", command="true")
        pipeline = Pipeline(name="ci", steps=["first", "second", "third"])

        executor = TaskExecutor(
            task_definitions={"first": task1, "second": task2, "third": task3, "ci": pipeline},
            dry_run=False,
        )

        result = executor.run("ci")
        assert isinstance(result, PipelineResult)
        assert result.short_circuited is False
        assert len(result.results) == 3
        assert result.exit_code == 0
        assert result.success is True

    def test_command_not_found_exit_code(self):
        """Command not found returns exit code 127."""
        task = Task(name="test", command="nonexistent_command_xyz123")
        executor = TaskExecutor(task_definitions={"test": task}, dry_run=False)

        result = executor.execute_task(task)
        assert result.exit_code == 127
        assert result.error is not None
        assert "not found" in result.error.lower()


class TestExecutionResult:
    """Tests for ExecutionResult dataclass."""

    def test_execution_result_creation(self):
        """ExecutionResult can be created with all fields."""
        result = ExecutionResult(
            task_name="test",
            exit_code=0,
            output="success",
            skipped=False,
            error=None,
        )
        assert result.task_name == "test"
        assert result.exit_code == 0
        assert result.output == "success"
        assert result.skipped is False
        assert result.error is None


class TestPipelineResult:
    """Tests for PipelineResult dataclass."""

    def test_pipeline_result_exit_code_success(self):
        """Pipeline exit code is 0 when all tasks succeed."""
        result = PipelineResult(
            pipeline_name="ci",
            results=[
                ExecutionResult(task_name="lint", exit_code=0),
                ExecutionResult(task_name="test", exit_code=0),
            ],
        )
        assert result.exit_code == 0
        assert result.success is True

    def test_pipeline_result_exit_code_failure(self):
        """Pipeline exit code is first failure's exit code."""
        result = PipelineResult(
            pipeline_name="ci",
            results=[
                ExecutionResult(task_name="lint", exit_code=0),
                ExecutionResult(task_name="test", exit_code=5),
            ],
        )
        assert result.exit_code == 5
        assert result.success is False

    def test_pipeline_result_short_circuited(self):
        """Pipeline tracks short-circuit state."""
        result = PipelineResult(
            pipeline_name="ci",
            results=[ExecutionResult(task_name="lint", exit_code=1)],
            short_circuited=True,
        )
        assert result.short_circuited is True


class TestCreateExecutorFromConfig:
    """Tests for create_executor_from_config helper."""

    def test_create_from_empty_config(self):
        """Empty config creates executor with no tasks."""
        executor = create_executor_from_config({})
        assert len(executor.task_definitions) == 0

    def test_create_from_task_config(self):
        """Task config is parsed correctly."""
        config = {
            "tasks": {
                "test": {
                    "command": "pytest",
                    "args": ["-v"],
                    "use_venv": True,
                }
            }
        }
        executor = create_executor_from_config(config)

        assert "test" in executor.task_definitions
        task = executor.task_definitions["test"]
        assert isinstance(task, Task)
        assert task.command == "pytest"
        assert task.args == ["-v"]
        assert task.use_venv is True

    def test_create_from_pipeline_config(self):
        """Pipeline config is parsed correctly."""
        config = {
            "tasks": {
                "lint": {"command": "ruff", "args": ["check", "."]},
                "test": {"command": "pytest"},
                "ci": {"pipeline": ["lint", "test"]},
            }
        }
        executor = create_executor_from_config(config)

        assert "ci" in executor.task_definitions
        pipeline = executor.task_definitions["ci"]
        assert isinstance(pipeline, Pipeline)
        assert pipeline.steps == ["lint", "test"]

    def test_create_with_env(self):
        """Task env is parsed correctly."""
        config = {
            "tasks": {
                "test": {
                    "command": "pytest",
                    "env": {"DEBUG": "1", "CI": "true"},
                }
            }
        }
        executor = create_executor_from_config(config)
        task = executor.task_definitions["test"]
        assert task.env == {"DEBUG": "1", "CI": "true"}

    def test_create_with_working_dir(self):
        """Task working_dir is parsed correctly."""
        config = {
            "tasks": {
                "test": {
                    "command": "pytest",
                    "working_dir": "tests",
                }
            }
        }
        executor = create_executor_from_config(config)
        task = executor.task_definitions["test"]
        assert task.working_dir == "tests"

    def test_create_with_options(self):
        """Executor options are set correctly."""
        config = {"tasks": {}}
        executor = create_executor_from_config(
            config,
            project_root=Path("/project"),
            dry_run=True,
            verbosity=2,
            venv_path=Path("/project/.venv"),
        )

        assert executor.project_root == Path("/project")
        assert executor.dry_run is True
        assert executor.verbosity == 2
        assert executor.venv_path == Path("/project/.venv")


class TestLogging:
    """Tests for executor logging."""

    def test_log_callback_called(self):
        """Log callback is called during execution."""
        logged_messages = []

        def log_callback(phase: str, message: str, level: int) -> None:
            logged_messages.append((phase, message, level))

        task = Task(name="test", command="echo", args=["hello"])
        executor = TaskExecutor(
            task_definitions={"test": task},
            dry_run=True,
            log_callback=log_callback,
        )

        executor.run("test")

        assert len(logged_messages) > 0
        phases = [m[0] for m in logged_messages]
        assert "test" in phases

    def test_verbosity_filtering(self):
        """Log messages are filtered by verbosity."""
        logged_messages = []

        def log_callback(phase: str, message: str, level: int) -> None:
            logged_messages.append((phase, message, level))

        task = Task(name="test", command="echo")
        executor = TaskExecutor(
            task_definitions={"test": task},
            dry_run=True,
            verbosity=-1,  # Quiet mode
            log_callback=log_callback,
        )

        executor.run("test")

        # Only level -1 messages should be logged in quiet mode
        for _, _, level in logged_messages:
            assert level <= -1
