"""Tests for CLI."""

from typer.testing import CliRunner

from devflow.cli import app

runner = CliRunner()


def test_help():
    """Test that --help works."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "devflow" in result.stdout
    assert "A Python-native project operations CLI" in result.stdout


def test_version():
    """Test that --version works."""
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "devflow version" in result.stdout


def test_stub_commands_exist():
    """Test that stub commands are available."""
    # Test venv command
    result = runner.invoke(app, ["venv", "--help"])
    assert result.exit_code == 0
    assert "venv" in result.stdout.lower()

    # Test deps command
    result = runner.invoke(app, ["deps", "--help"])
    assert result.exit_code == 0
    assert "deps" in result.stdout.lower()

    # Test test command
    result = runner.invoke(app, ["test", "--help"])
    assert result.exit_code == 0
    assert "test" in result.stdout.lower()

    # Test build command
    result = runner.invoke(app, ["build", "--help"])
    assert result.exit_code == 0
    assert "build" in result.stdout.lower()

    # Test publish command
    result = runner.invoke(app, ["publish", "--help"])
    assert result.exit_code == 0
    assert "publish" in result.stdout.lower()

    # Test git command
    result = runner.invoke(app, ["git", "--help"])
    assert result.exit_code == 0
    assert "git" in result.stdout.lower()

    # Test task command
    result = runner.invoke(app, ["task", "--help"])
    assert result.exit_code == 0
    assert "task" in result.stdout.lower()


def test_global_flags():
    """Test that global flags are recognized."""
    # Test verbose flag
    result = runner.invoke(app, ["-v", "test"])
    assert result.exit_code == 0

    # Test quiet flag
    result = runner.invoke(app, ["-q", "test"])
    assert result.exit_code == 0

    # Test dry-run flag
    result = runner.invoke(app, ["--dry-run", "test"])
    assert result.exit_code == 0
