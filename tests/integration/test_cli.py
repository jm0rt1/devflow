"""Integration tests for CLI functionality."""

import subprocess
import tempfile
from pathlib import Path

import pytest


class TestCLI:
    """Test CLI integration."""

    def test_version_flag(self):
        """Test --version flag."""
        result = subprocess.run(
            ["devflow", "--version"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "devflow version" in result.stdout

    def test_help_flag(self):
        """Test --help flag."""
        result = subprocess.run(
            ["devflow", "--help"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "devflow" in result.stdout
        assert "Usage:" in result.stdout

    def test_no_args_lists_commands(self):
        """Test that running devflow with no args lists commands."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a minimal pyproject.toml
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")
            
            result = subprocess.run(
                ["devflow"],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "Core Commands:" in result.stdout
            assert "venv" in result.stdout
            assert "deps" in result.stdout
            assert "test" in result.stdout
            assert "build" in result.stdout
            assert "completion" in result.stdout
            assert "Global Options:" in result.stdout

    def test_no_args_lists_project_tasks(self):
        """Test that no args lists project-specific tasks from config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("""
[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]

[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test"]
""")
            
            result = subprocess.run(
                ["devflow"],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "Project Tasks:" in result.stdout
            assert "lint" in result.stdout
            assert "ci-check" in result.stdout
            assert "Pipeline: lint, test" in result.stdout

    def test_completion_bash(self):
        """Test bash completion generation."""
        result = subprocess.run(
            ["devflow", "completion", "bash"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "_devflow_completion" in result.stdout
        assert "complete -F" in result.stdout

    def test_completion_zsh(self):
        """Test zsh completion generation."""
        result = subprocess.run(
            ["devflow", "completion", "zsh"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "#compdef devflow" in result.stdout
        assert "_devflow()" in result.stdout

    def test_completion_fish(self):
        """Test fish completion generation."""
        result = subprocess.run(
            ["devflow", "completion", "fish"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0
        assert "complete -c devflow" in result.stdout

    def test_completion_unsupported_shell(self):
        """Test error handling for unsupported shell."""
        result = subprocess.run(
            ["devflow", "completion", "powershell"],
            capture_output=True,
            text=True
        )
        assert result.returncode == 1
        assert "Unsupported shell" in result.stderr or "Unsupported shell" in result.stdout

    def test_command_help(self):
        """Test help for individual commands."""
        commands = ["venv", "deps", "test", "build", "task", "completion"]
        
        for cmd in commands:
            result = subprocess.run(
                ["devflow", cmd, "--help"],
                capture_output=True,
                text=True
            )
            assert result.returncode == 0, f"Failed for command: {cmd}"
            assert "Usage:" in result.stdout, f"No usage info for: {cmd}"
            assert "Examples:" in result.stdout or "help" in result.stdout.lower(), \
                f"No examples/help for: {cmd}"

    def test_verbose_flag(self):
        """Test -v/--verbose flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")
            
            result = subprocess.run(
                ["devflow", "-vv", "test"],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            # Test exits successfully (stub implementation)
            assert result.returncode == 0

    def test_dry_run_flag(self):
        """Test --dry-run flag."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")
            
            result = subprocess.run(
                ["devflow", "--dry-run", "build"],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            assert result.returncode == 0

    def test_config_flag(self):
        """Test --config flag with explicit config file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config_file = project_root / "custom.toml"
            config_file.write_text("""
[devflow]
test_runner = "unittest"

[devflow.tasks.mytask]
command = "echo"
args = ["hello"]
""")
            # Also create a pyproject.toml so project root can be found
            (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")
            
            result = subprocess.run(
                ["devflow", "--config", str(config_file)],
                cwd=tmpdir,
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            assert "mytask" in result.stdout
