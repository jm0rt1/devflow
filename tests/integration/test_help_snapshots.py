"""Snapshot tests for help output to ensure consistency."""

import subprocess
from pathlib import Path
import tempfile

import pytest


class TestHelpSnapshots:
    """Test that help output remains consistent and comprehensive."""

    def test_main_help_contains_expected_sections(self):
        """Test that main help contains all expected sections."""
        result = subprocess.run(
            ["devflow", "--help"],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "NO_COLOR": "1"}  # Disable ANSI colors
        )
        
        assert result.returncode == 0
        help_text = result.stdout
        
        # Check for key sections
        assert "Usage:" in help_text
        assert "Options:" in help_text or "Commands:" in help_text
        
        # Check for all core commands
        expected_commands = ["venv", "deps", "test", "build", "task", "completion"]
        for cmd in expected_commands:
            assert cmd in help_text, f"Command '{cmd}' not in help output"

    def test_venv_help_has_examples(self):
        """Test that venv help includes usage examples."""
        result = subprocess.run(
            ["devflow", "venv", "--help"],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        help_text = result.stdout
        
        # Should have examples section or inline examples
        assert "devflow venv init" in help_text
        
        # Should document options
        assert "python" in help_text.lower()
        assert "recreate" in help_text.lower()

    def test_deps_help_has_examples(self):
        """Test that deps help includes usage examples."""
        result = subprocess.run(
            ["devflow", "deps", "--help"],
            capture_output=True,
            text=True,
            env={**subprocess.os.environ, "NO_COLOR": "1"}
        )
        
        assert result.returncode == 0
        help_text = result.stdout
        
        # Should document the subcommands
        assert "sync" in help_text
        assert "freeze" in help_text

    def test_task_help_has_config_examples(self):
        """Test that task help includes configuration examples."""
        result = subprocess.run(
            ["devflow", "task", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        help_text = result.stdout
        
        # Should show how to define tasks (check for key content)
        assert "tool.devflow.tasks" in help_text
        assert "command" in help_text.lower()
        assert "pipeline" in help_text.lower()

    def test_completion_help_has_installation_instructions(self):
        """Test that completion help includes installation instructions."""
        result = subprocess.run(
            ["devflow", "completion", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        help_text = result.stdout
        
        # Should document all supported shells
        assert "bash" in help_text.lower()
        assert "zsh" in help_text.lower()
        assert "fish" in help_text.lower()
        
        # Should have installation examples or eval mention
        assert "eval" in help_text.lower() or "install" in help_text.lower()

    def test_no_args_output_format(self):
        """Test the format of output when no args provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("""
[tool.devflow.tasks.lint]
command = "ruff"

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
            output = result.stdout
            
            # Check structure
            assert "devflow - A Python-native project operations CLI" in output
            assert "Usage:" in output
            assert "Core Commands:" in output
            assert "Project Tasks:" in output
            assert "Global Options:" in output
            
            # Check task formatting
            assert "ci-check" in output
            assert "Pipeline: lint, test" in output
            assert "lint" in output
            assert "Command: ruff" in output

    def test_global_options_documented_consistently(self):
        """Test that global options are documented in all command helps."""
        commands = ["venv", "deps", "test", "build", "task"]
        
        for cmd in commands:
            result = subprocess.run(
                ["devflow", cmd, "--help"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            # Typer adds standard options, just verify help works
            assert "Usage:" in result.stdout
            assert "--help" in result.stdout

    def test_help_shows_version_info_location(self):
        """Test that users can find version information."""
        result = subprocess.run(
            ["devflow", "--help"],
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0
        # Should document --version flag
        assert "--version" in result.stdout

    def test_examples_use_consistent_format(self):
        """Test that examples across commands use consistent formatting."""
        commands = ["venv", "deps", "task", "completion"]
        
        for cmd in commands:
            result = subprocess.run(
                ["devflow", cmd, "--help"],
                capture_output=True,
                text=True
            )
            
            assert result.returncode == 0
            help_text = result.stdout.lower()
            
            # Should show command invocations
            assert "devflow" in help_text
            # Should have comments or examples
            assert "#" in help_text or "example" in help_text
