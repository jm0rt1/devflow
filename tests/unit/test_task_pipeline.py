"""Tests for Task and Pipeline abstractions."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devflow.app import AppContext
from devflow.commands.base import Pipeline, Task


@pytest.fixture
def mock_app():
    """Create a mock app context."""
    app = MagicMock(spec=AppContext)
    app.dry_run = False
    app.project_root = Path("/fake/project")
    app.venv_path = Path("/fake/project/.venv")
    app.logger = MagicMock()
    return app


def test_task_creation():
    """Test creating a Task object."""
    task = Task(
        name="test-task",
        command=["echo", "hello"],
        use_venv=True,
        env={"FOO": "bar"},
    )

    assert task.name == "test-task"
    assert task.command == ["echo", "hello"]
    assert task.use_venv is True
    assert task.env == {"FOO": "bar"}


@patch("subprocess.run")
def test_task_execute_success(mock_run, mock_app):
    """Test executing a task that succeeds."""
    mock_run.return_value = MagicMock(returncode=0)

    task = Task(name="test", command=["echo", "hello"])
    exit_code = task.execute(mock_app)

    assert exit_code == 0
    mock_run.assert_called_once()
    assert mock_run.call_args[0][0] == ["echo", "hello"]


@patch("subprocess.run")
def test_task_execute_failure(mock_run, mock_app):
    """Test executing a task that fails."""
    mock_run.return_value = MagicMock(returncode=1)

    task = Task(name="test", command=["false"])
    exit_code = task.execute(mock_app)

    assert exit_code == 1
    mock_app.logger.error.assert_called()


def test_task_execute_dry_run(mock_app):
    """Test executing a task in dry-run mode."""
    mock_app.dry_run = True

    task = Task(name="test", command=["rm", "-rf", "/"])
    exit_code = task.execute(mock_app)

    assert exit_code == 0
    mock_app.logger.info.assert_called()
    # Verify the command was logged but not executed


@patch("subprocess.run")
def test_task_with_env(mock_run, mock_app):
    """Test task execution with custom environment variables."""
    mock_run.return_value = MagicMock(returncode=0)

    task = Task(
        name="test",
        command=["env"],
        env={"CUSTOM_VAR": "custom_value"}
    )
    exit_code = task.execute(mock_app)

    assert exit_code == 0
    # Check that env was passed
    call_kwargs = mock_run.call_args[1]
    assert "env" in call_kwargs
    assert call_kwargs["env"]["CUSTOM_VAR"] == "custom_value"


def test_pipeline_creation():
    """Test creating a Pipeline object."""
    task1 = Task(name="task1", command=["echo", "1"])
    task2 = Task(name="task2", command=["echo", "2"])

    pipeline = Pipeline(name="test-pipeline", tasks=[task1, task2])

    assert pipeline.name == "test-pipeline"
    assert len(pipeline.tasks) == 2


@patch("subprocess.run")
def test_pipeline_execute_all_succeed(mock_run, mock_app):
    """Test pipeline execution when all tasks succeed."""
    mock_run.return_value = MagicMock(returncode=0)

    task1 = Task(name="task1", command=["echo", "1"])
    task2 = Task(name="task2", command=["echo", "2"])
    pipeline = Pipeline(name="test-pipeline", tasks=[task1, task2])

    exit_code = pipeline.execute(mock_app)

    assert exit_code == 0
    assert mock_run.call_count == 2


@patch("subprocess.run")
def test_pipeline_stops_on_failure(mock_run, mock_app):
    """Test that pipeline stops at first failure."""
    # First task fails, second succeeds
    mock_run.side_effect = [
        MagicMock(returncode=1),  # task1 fails
        MagicMock(returncode=0),  # task2 would succeed
    ]

    task1 = Task(name="task1", command=["false"])
    task2 = Task(name="task2", command=["echo", "2"])
    pipeline = Pipeline(name="test-pipeline", tasks=[task1, task2])

    exit_code = pipeline.execute(mock_app)

    assert exit_code == 1
    # Only first task should be executed
    assert mock_run.call_count == 1
    mock_app.logger.error.assert_called()


@patch("subprocess.run")
def test_pipeline_dry_run(mock_run, mock_app):
    """Test pipeline execution in dry-run mode."""
    mock_app.dry_run = True

    task1 = Task(name="task1", command=["rm", "-rf", "/"])
    task2 = Task(name="task2", command=["rm", "-rf", "/home"])
    pipeline = Pipeline(name="dangerous-pipeline", tasks=[task1, task2])

    exit_code = pipeline.execute(mock_app)

    assert exit_code == 0
    # No actual subprocess calls should happen
    mock_run.assert_not_called()


def test_empty_pipeline(mock_app):
    """Test executing an empty pipeline."""
    pipeline = Pipeline(name="empty", tasks=[])
    exit_code = pipeline.execute(mock_app)

    assert exit_code == 0
