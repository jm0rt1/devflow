"""Tests for TaskCommand - the 'devflow task <name>' CLI command.

Ownership: Workstream B (task/registry)
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from devflow.commands.task_command import TaskCommand, create_task_typer_command


class MockConfig:
    """Mock config for testing (real one is owned by Workstream A)."""

    def __init__(self, tasks=None, venv_dir=".venv"):
        self.tasks = tasks or {}
        self.venv_dir = venv_dir

    def to_dict(self):
        return {"tasks": self.tasks}


class MockAppContext:
    """Mock AppContext for testing (real one is owned by Workstream A)."""

    def __init__(self, tasks=None, dry_run=False, verbosity=0):
        self.project_root = Path("/test/project")
        self.config = MockConfig(tasks=tasks)
        self.dry_run = dry_run
        self.verbosity = verbosity


class TestTaskCommand:
    """Tests for the TaskCommand class."""

    def test_task_command_attributes(self):
        """TaskCommand has correct name and help."""
        app = MockAppContext()
        cmd = TaskCommand(app)

        assert cmd.name == "task"
        assert "task" in cmd.help.lower() or "custom" in cmd.help.lower()

    def test_list_tasks_empty(self):
        """list_tasks returns empty list when no tasks defined."""
        app = MockAppContext(tasks={})
        cmd = TaskCommand(app)

        assert cmd.list_tasks() == []

    def test_list_tasks_returns_sorted(self):
        """list_tasks returns tasks in sorted order."""
        app = MockAppContext(
            tasks={
                "zebra": {"command": "echo", "args": ["zebra"]},
                "alpha": {"command": "echo", "args": ["alpha"]},
                "middle": {"command": "echo", "args": ["middle"]},
            }
        )
        cmd = TaskCommand(app)

        tasks = cmd.list_tasks()
        assert tasks == ["alpha", "middle", "zebra"]

    def test_run_list_tasks_flag(self, capsys):
        """run with list_tasks=True lists available tasks."""
        app = MockAppContext(
            tasks={
                "test": {"command": "pytest"},
                "lint": {"command": "ruff"},
            }
        )
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name=None, list_tasks=True)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "test" in captured.out
        assert "lint" in captured.out

    def test_run_no_task_name_lists_tasks(self, capsys):
        """run without task_name lists available tasks."""
        app = MockAppContext(
            tasks={
                "test": {"command": "pytest"},
            }
        )
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name=None)

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "test" in captured.out

    def test_run_task_not_found(self, capsys):
        """run with nonexistent task returns error."""
        app = MockAppContext(tasks={"test": {"command": "pytest"}})
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name="missing")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "missing" in captured.err.lower()

    def test_run_task_dry_run(self):
        """run in dry-run mode doesn't execute."""
        app = MockAppContext(
            tasks={"test": {"command": "pytest", "args": ["-v"]}},
            dry_run=True,
        )
        cmd = TaskCommand(app)

        # Should complete without actually running pytest
        exit_code = cmd.run(task_name="test")

        assert exit_code == 0

    @patch("subprocess.run")
    def test_run_task_success(self, mock_run):
        """run with valid task executes and returns success."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        app = MockAppContext(
            tasks={"test": {"command": "echo", "args": ["hello"]}},
            dry_run=False,
        )
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name="test")

        assert exit_code == 0
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_task_failure(self, mock_run):
        """run with failing task returns error code."""
        mock_run.return_value = MagicMock(returncode=42, stdout="", stderr="")

        app = MockAppContext(
            tasks={"test": {"command": "false"}},
            dry_run=False,
        )
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name="test")

        assert exit_code == 42

    @patch("subprocess.run")
    def test_run_pipeline(self, mock_run):
        """run with pipeline executes all steps."""
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        app = MockAppContext(
            tasks={
                "lint": {"command": "ruff"},
                "test": {"command": "pytest"},
                "ci": {"pipeline": ["lint", "test"]},
            },
            dry_run=False,
        )
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name="ci")

        assert exit_code == 0
        assert mock_run.call_count == 2

    def test_run_cycle_detection(self, capsys):
        """run detects cycles in pipeline definitions."""
        app = MockAppContext(
            tasks={
                "a": {"pipeline": ["b"]},
                "b": {"pipeline": ["a"]},
            }
        )
        cmd = TaskCommand(app)

        exit_code = cmd.run(task_name="a")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "cycle" in captured.err.lower()


class TestCreateTaskTyperCommand:
    """Tests for the create_task_typer_command factory."""

    def test_creates_callable(self):
        """create_task_typer_command returns a callable."""
        app = MockAppContext()
        callback = create_task_typer_command(app)

        assert callable(callback)

    def test_callback_list_tasks(self, capsys):
        """Typer callback supports list_tasks."""
        app = MockAppContext(
            tasks={"test": {"command": "pytest"}},
        )
        callback = create_task_typer_command(app)

        # Should not raise
        callback(task_name=None, list_tasks=True)

        captured = capsys.readouterr()
        assert "test" in captured.out

    def test_callback_raises_system_exit_on_failure(self):
        """Typer callback raises SystemExit on failure."""
        app = MockAppContext(tasks={})
        callback = create_task_typer_command(app)

        with pytest.raises(SystemExit) as exc_info:
            callback(task_name="missing", list_tasks=False)

        assert exc_info.value.code == 1
