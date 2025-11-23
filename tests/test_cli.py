"""Tests for the CLI module."""

import subprocess
import sys

from typer.testing import CliRunner

from devflow import __version__
from devflow.cli import app

runner = CliRunner()


def test_version_flag():
    """Test --version flag displays version."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_help_flag():
    """Test --help flag displays help."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "devflow" in result.stdout.lower()
    assert "usage" in result.stdout.lower() or "options" in result.stdout.lower()


def test_no_args_shows_help():
    """Test that running with no args shows help."""
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    # Typer's no_args_is_help should trigger help display


def test_venv_command():
    """Test venv command exists."""
    result = runner.invoke(app, ["venv"])
    assert "not yet implemented" in result.stdout.lower()
    assert result.exit_code == 1


def test_deps_command():
    """Test deps command exists."""
    result = runner.invoke(app, ["deps"])
    assert "not yet implemented" in result.stdout.lower()
    assert result.exit_code == 1


def test_test_command():
    """Test test command exists."""
    result = runner.invoke(app, ["test"])
    assert "not yet implemented" in result.stdout.lower()
    assert result.exit_code == 1


def test_build_command():
    """Test build command exists."""
    result = runner.invoke(app, ["build"])
    assert "not yet implemented" in result.stdout.lower()
    assert result.exit_code == 1


def test_publish_command():
    """Test publish command exists."""
    result = runner.invoke(app, ["publish"])
    assert "not yet implemented" in result.stdout.lower()
    assert result.exit_code == 1


def test_task_command():
    """Test task command exists."""
    result = runner.invoke(app, ["task", "mytask"])
    assert "not yet implemented" in result.stdout.lower()
    assert "mytask" in result.stdout
    assert result.exit_code == 1


def test_global_flags_accepted():
    """Test that global flags are accepted."""
    # Test --dry-run flag
    result = runner.invoke(app, ["--dry-run", "test"])
    assert result.exit_code == 1  # Command not implemented, but flag accepted

    # Test --verbose flag
    result = runner.invoke(app, ["-v", "test"])
    assert result.exit_code == 1

    result = runner.invoke(app, ["-vv", "test"])
    assert result.exit_code == 1

    # Test --quiet flag
    result = runner.invoke(app, ["--quiet", "test"])
    assert result.exit_code == 1


def test_cli_main_entry_point():
    """Test that the CLI entry point works."""
    result = subprocess.run(
        [sys.executable, "-m", "devflow.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert __version__ in result.stdout


def test_config_flag_accepted():
    """Test --config flag is accepted."""
    result = runner.invoke(app, ["--config", "test.toml", "test"])
    assert result.exit_code == 1  # Command not implemented


def test_project_root_flag_accepted():
    """Test --project-root flag is accepted."""
    result = runner.invoke(app, ["--project-root", "/tmp", "test"])
    assert result.exit_code == 1  # Command not implemented
