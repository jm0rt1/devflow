"""Tests for CLI interface."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from devflow import __version__
from devflow.cli import app

runner = CliRunner()


class TestCLIVersion:
    """Tests for --version flag."""

    def test_version_flag(self) -> None:
        """Should print version and exit."""
        result = runner.invoke(app, ["--version"])

        assert result.exit_code == 0
        assert __version__ in result.stdout


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    import re
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


class TestCLIHelp:
    """Tests for help output."""

    def test_help_flag(self) -> None:
        """Should show help when --help is passed."""
        result = runner.invoke(app, ["--help"])
        output = strip_ansi(result.stdout)

        assert result.exit_code == 0
        assert "devflow" in output.lower()
        assert "--config" in output or "config" in output.lower()
        assert "--project-root" in output or "project-root" in output.lower()
        assert "--dry-run" in output or "dry-run" in output.lower()
        assert "--verbose" in output or "verbose" in output.lower()
        assert "--quiet" in output or "quiet" in output.lower()

    def test_no_args_shows_commands(self, tmp_path: Path) -> None:
        """Should show available commands when no args provided."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        with patch("devflow.cli.Path.cwd", return_value=tmp_path):
            result = runner.invoke(app, [], env={"PWD": str(tmp_path)})

        # Should show available commands
        assert "venv" in result.stdout.lower() or "command" in result.stdout.lower()


class TestCLIGlobalFlags:
    """Tests for global CLI flags."""

    def test_dry_run_flag(self, tmp_path: Path) -> None:
        """Should accept --dry-run flag."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = runner.invoke(app, ["--project-root", str(tmp_path), "--dry-run", "test"])

        # Should not error
        assert result.exit_code == 0

    def test_verbose_flag(self, tmp_path: Path) -> None:
        """Should accept -v/--verbose flag."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = runner.invoke(app, ["--project-root", str(tmp_path), "-v", "test"])

        assert result.exit_code == 0

    def test_quiet_flag(self, tmp_path: Path) -> None:
        """Should accept -q/--quiet flag."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = runner.invoke(app, ["--project-root", str(tmp_path), "--quiet", "test"])

        assert result.exit_code == 0

    def test_config_flag(self, tmp_path: Path) -> None:
        """Should accept --config flag."""
        config_path = tmp_path / "custom.toml"
        config_path.write_text("[devflow]\nvenv_dir = '.custom'\n")
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = runner.invoke(
            app,
            ["--project-root", str(tmp_path), "--config", str(config_path), "test"]
        )

        assert result.exit_code == 0

    def test_project_root_flag(self, tmp_path: Path) -> None:
        """Should accept --project-root flag."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = runner.invoke(app, ["--project-root", str(tmp_path), "test"])

        assert result.exit_code == 0


class TestCLISubcommands:
    """Tests for subcommand registration."""

    def test_venv_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have venv subcommand."""
        result = runner.invoke(app, ["venv", "--help"])

        assert result.exit_code == 0
        assert "venv" in result.stdout.lower() or "environment" in result.stdout.lower()

    def test_deps_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have deps subcommand."""
        result = runner.invoke(app, ["deps", "--help"])

        assert result.exit_code == 0

    def test_test_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have test subcommand."""
        result = runner.invoke(app, ["test", "--help"])

        assert result.exit_code == 0

    def test_build_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have build subcommand."""
        result = runner.invoke(app, ["build", "--help"])

        assert result.exit_code == 0

    def test_publish_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have publish subcommand."""
        result = runner.invoke(app, ["publish", "--help"])

        assert result.exit_code == 0

    def test_git_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have git subcommand."""
        result = runner.invoke(app, ["git", "--help"])

        assert result.exit_code == 0

    def test_task_subcommand_exists(self, tmp_path: Path) -> None:
        """Should have task subcommand."""
        result = runner.invoke(app, ["task", "--help"])

        assert result.exit_code == 0


class TestCLIErrorHandling:
    """Tests for CLI error handling."""

    def test_invalid_config_path(self, tmp_path: Path) -> None:
        """Should show error for invalid config path."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        nonexistent = tmp_path / "nonexistent.toml"

        result = runner.invoke(
            app,
            ["--project-root", str(tmp_path), "--config", str(nonexistent), "test"]
        )

        assert result.exit_code != 0
        assert "not found" in result.stdout.lower() or "error" in result.stdout.lower()

    def test_invalid_project_root(self, tmp_path: Path) -> None:
        """Should show error for invalid project root."""
        nonexistent = tmp_path / "nonexistent"

        result = runner.invoke(app, ["--project-root", str(nonexistent), "test"])

        assert result.exit_code != 0
