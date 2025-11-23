"""Integration tests for the test command."""

from pathlib import Path

from devflow.app import AppContext
from devflow.commands.test import test_command


def test_test_command_requires_venv(temp_project: Path):
    """Test that test command requires a venv to exist."""
    app = AppContext(project_root=temp_project, quiet=True)

    result = test_command(app)

    assert result == 1


def test_test_command_runs_pytest(venv_project: Path):
    """Test that test command runs pytest successfully."""
    app = AppContext(project_root=venv_project, quiet=True)

    result = test_command(app)

    assert result == 0


def test_test_command_passes_args(venv_project: Path):
    """Test that test command passes arguments to pytest."""
    app = AppContext(project_root=venv_project, verbosity=1)

    # Run with verbose flag
    result = test_command(app, args=["-v"])

    assert result == 0


def test_test_command_dry_run(venv_project: Path):
    """Test that test command respects dry-run mode."""
    app = AppContext(project_root=venv_project, dry_run=True, verbosity=1)

    result = test_command(app)

    # Dry run always succeeds
    assert result == 0


def test_test_command_failing_tests(venv_project: Path):
    """Test that test command returns non-zero exit code for failing tests."""
    # Add a failing test
    tests_dir = venv_project / "tests"
    (tests_dir / "test_failing.py").write_text("""
def test_failing():
    assert False
""")

    app = AppContext(project_root=venv_project, quiet=True)

    result = test_command(app)

    # Should fail
    assert result != 0
