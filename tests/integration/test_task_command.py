"""Integration tests for task command execution."""


import pytest

from devflow.app import AppContext
from devflow.commands.custom import TaskCommand
from devflow.config import AppConfig, TaskConfig


@pytest.fixture
def temp_project(tmp_path):
    """Create a temporary project directory."""
    project = tmp_path / "test-project"
    project.mkdir()

    # Create a minimal pyproject.toml
    pyproject = project / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
""")

    return project


def test_task_command_simple_task(temp_project):
    """Test executing a simple task."""
    # Create app context with test configuration
    config = AppConfig(
        tasks={
            "hello": TaskConfig(
                command="echo",
                args=["Hello, World!"],
                use_venv=False,
            )
        }
    )

    app = AppContext(project_root=temp_project, verbosity=0)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("hello")

    assert exit_code == 0


def test_task_command_pipeline(temp_project):
    """Test executing a pipeline task."""
    config = AppConfig(
        tasks={
            "ci": TaskConfig(pipeline=["step1", "step2"]),
            "step1": TaskConfig(command="echo", args=["Step 1"], use_venv=False),
            "step2": TaskConfig(command="echo", args=["Step 2"], use_venv=False),
        }
    )

    app = AppContext(project_root=temp_project, verbosity=0)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("ci")

    assert exit_code == 0


def test_task_command_pipeline_fails_on_error(temp_project):
    """Test that pipeline stops on first error."""
    config = AppConfig(
        tasks={
            "ci": TaskConfig(pipeline=["step1", "step2"]),
            "step1": TaskConfig(command="false", use_venv=False),  # This will fail
            "step2": TaskConfig(command="echo", args=["Should not run"], use_venv=False),
        }
    )

    app = AppContext(project_root=temp_project, verbosity=0)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("ci")

    assert exit_code != 0


def test_task_command_not_found(temp_project):
    """Test error when task is not found."""
    config = AppConfig(tasks={})

    app = AppContext(project_root=temp_project, verbosity=0)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("nonexistent")

    assert exit_code != 0


def test_task_command_cycle_detection(temp_project):
    """Test that cycles are detected and reported."""
    config = AppConfig(
        tasks={
            "a": TaskConfig(pipeline=["b"]),
            "b": TaskConfig(pipeline=["a"]),
        }
    )

    app = AppContext(project_root=temp_project, verbosity=0)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("a")

    assert exit_code != 0


def test_task_command_dry_run(temp_project):
    """Test task execution in dry-run mode."""
    config = AppConfig(
        tasks={
            "dangerous": TaskConfig(
                command="rm",
                args=["-rf", "/"],
                use_venv=False,
            )
        }
    )

    app = AppContext(project_root=temp_project, verbosity=1, dry_run=True)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("dangerous")

    # Should succeed without actually running the command
    assert exit_code == 0


def test_task_command_with_env(temp_project):
    """Test task with custom environment variables."""
    # Create a shell script that checks for env var
    script = temp_project / "check_env.sh"
    script.write_text("#!/bin/bash\nif [ \"$TEST_VAR\" = \"test_value\" ]; then exit 0; else exit 1; fi\n")
    script.chmod(0o755)

    config = AppConfig(
        tasks={
            "check": TaskConfig(
                command=str(script),
                env={"TEST_VAR": "test_value"},
                use_venv=False,
            )
        }
    )

    app = AppContext(project_root=temp_project, verbosity=0)
    app.config = config

    cmd = TaskCommand(app)
    exit_code = cmd.run("check")

    assert exit_code == 0
