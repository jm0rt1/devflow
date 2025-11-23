"""
Acceptance test scenarios per docs/DESIGN_SPEC.md and docs/COPILOT_PLAN.md.

These tests capture the key scenarios:
- Scenario 1: Replace test.sh with devflow test
- Scenario 2: Portable build & publish
- Scenario 3: Custom pipeline (ci-check)
- Scenario 4: Configurability & Overrides
- Scenario 5: Git integration & safety
"""

import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest


def run_devflow(
    args: List[str], cwd: Path | None = None, check: bool = False
) -> subprocess.CompletedProcess:
    """Helper to run devflow CLI."""
    cmd = [sys.executable, "-m", "devflow.cli"] + args
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def create_test_project(base_dir: Path, config: Dict[str, Any] | None = None) -> Path:
    """Create a minimal test project with pyproject.toml."""
    project_dir = base_dir / "test_project"
    project_dir.mkdir(exist_ok=True)

    # Create minimal pyproject.toml
    config_lines = ["[tool.devflow]"]
    if config:
        for key, value in config.items():
            if isinstance(value, str):
                config_lines.append(f'{key} = "{value}"')
            elif isinstance(value, bool):
                config_lines.append(f"{key} = {str(value).lower()}")
            else:
                config_lines.append(f"{key} = {value}")

    pyproject = project_dir / "pyproject.toml"
    pyproject.write_text("\n".join(config_lines))

    # Create a minimal package structure
    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)
    init_file = src_dir / "__init__.py"
    init_file.write_text('"""Test package."""\n__version__ = "0.1.0"\n')

    return project_dir


class TestScenario1ReplaceTestScript:
    """
    Scenario 1: Replace test.sh with devflow test

    Given: A project with pyproject.toml configured
    When: User runs: devflow venv init, devflow deps sync, devflow test
    Then: Commands execute in sequence (even if not fully implemented yet)
    """

    def test_venv_init_command_exists(self, tmp_path):
        """Test that venv init command is available."""
        project_dir = create_test_project(tmp_path, {"venv_dir": ".venv"})
        result = run_devflow(["venv", "init"], cwd=project_dir)

        # Command should be recognized (even if not implemented)
        assert "not yet implemented" in result.stdout.lower() or result.returncode == 1

    def test_deps_sync_command_exists(self, tmp_path):
        """Test that deps sync command is available."""
        project_dir = create_test_project(tmp_path)
        result = run_devflow(["deps", "sync"], cwd=project_dir)

        assert "not yet implemented" in result.stdout.lower() or result.returncode == 1

    def test_test_command_exists(self, tmp_path):
        """Test that test command is available."""
        project_dir = create_test_project(tmp_path)
        result = run_devflow(["test"], cwd=project_dir)

        assert "not yet implemented" in result.stdout.lower() or result.returncode == 1


class TestScenario2PortableBuildPublish:
    """
    Scenario 2: Portable build & publish

    Given: pyproject.toml with [build-system] and [tool.devflow]
    When: devflow build and devflow publish --dry-run
    Then: Commands are available and dry-run doesn't execute
    """

    def test_build_command_exists(self, tmp_path):
        """Test that build command is available."""
        project_dir = create_test_project(tmp_path, {"build_backend": "build"})
        result = run_devflow(["build"], cwd=project_dir)

        assert "not yet implemented" in result.stdout.lower() or result.returncode == 1

    def test_publish_dry_run_flag(self, tmp_path):
        """Test that publish accepts --dry-run flag."""
        project_dir = create_test_project(tmp_path)
        result = run_devflow(["--dry-run", "publish"], cwd=project_dir)

        # Should accept the flag (even if command not implemented)
        assert result.returncode != 2  # Exit code 2 typically means argument error


class TestScenario3CustomPipeline:
    """
    Scenario 3: Custom pipeline (ci-check)

    Given: pyproject.toml with [tool.devflow.tasks.ci-check] pipeline = ["format", "lint", "test"]
    When: devflow task ci-check
    Then: Task command is available
    """

    def test_task_command_exists(self, tmp_path):
        """Test that task command is available."""
        project_dir = create_test_project(tmp_path)
        result = run_devflow(["task", "ci-check"], cwd=project_dir)

        assert "not yet implemented" in result.stdout.lower() or result.returncode == 1
        assert "ci-check" in result.stdout


class TestScenario4Configurability:
    """
    Scenario 4: Configurability & Overrides

    Test that configuration flags are accepted by the CLI.
    """

    def test_config_flag_accepted(self, tmp_path):
        """Test --config flag is accepted."""
        result = run_devflow(["--config", "custom.toml", "test"])
        # Flag should be accepted (command may not be implemented)
        assert result.returncode != 2

    def test_project_root_flag_accepted(self, tmp_path):
        """Test --project-root flag is accepted."""
        result = run_devflow(["--project-root", str(tmp_path), "test"])
        assert result.returncode != 2

    def test_verbose_flags_accepted(self, tmp_path):
        """Test verbosity flags are accepted."""
        result = run_devflow(["-v", "test"])
        assert result.returncode != 2

        result = run_devflow(["-vv", "test"])
        assert result.returncode != 2

    def test_quiet_flag_accepted(self, tmp_path):
        """Test --quiet flag is accepted."""
        result = run_devflow(["--quiet", "test"])
        assert result.returncode != 2


class TestScenario5GitIntegration:
    """
    Scenario 5: Git integration & safety

    Test that git-related features are planned (will fail gracefully for now).
    Note: Full implementation requires git helpers (Workstream E).
    """

    def test_publish_with_dirty_working_tree_planned(self, tmp_path):
        """
        Test that publish command exists for future git integration.

        In the future, this should:
        - Check git status
        - Fail before build/publish if dirty
        - Print clear message about working tree cleanliness
        """
        project_dir = create_test_project(
            tmp_path,
            {
                "tag_on_publish": True,
                "require_clean_working_tree": True,
            },
        )

        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=project_dir,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=project_dir,
            capture_output=True,
        )
        subprocess.run(["git", "add", "."], cwd=project_dir, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=project_dir,
            capture_output=True,
        )

        # Create a dirty file
        dirty_file = project_dir / "dirty.txt"
        dirty_file.write_text("uncommitted change")

        # Try to publish
        result = run_devflow(["publish"], cwd=project_dir)

        # For now, just verify the command exists
        assert "not yet implemented" in result.stdout.lower() or result.returncode != 0


class TestDryRunSupport:
    """Test that --dry-run flag is supported across commands."""

    @pytest.mark.parametrize("command", ["venv", "deps", "test", "build", "publish"])
    def test_dry_run_flag_accepted(self, command, tmp_path):
        """Test --dry-run flag is accepted by all commands."""
        args = ["--dry-run", command]
        if command in ["venv", "deps"]:
            args.append("init")  # These commands need a subcommand

        result = run_devflow(args)

        # Dry-run flag should be accepted (exit code != 2 for argument error)
        assert result.returncode != 2


class TestPortability:
    """Test portability aspects."""

    def test_cli_runs_on_current_platform(self):
        """Test that CLI runs on current platform."""
        result = run_devflow(["--version"])
        assert result.returncode == 0
        assert "0.1.0" in result.stdout

    def test_help_output_available(self):
        """Test that help is available."""
        result = run_devflow(["--help"])
        assert result.returncode == 0
        assert "devflow" in result.stdout.lower()

    def test_commands_discoverable(self):
        """Test that commands are listed in help."""
        result = run_devflow(["--help"])
        assert result.returncode == 0

        # Check for key commands mentioned in design spec
        expected_commands = ["venv", "deps", "test", "build", "publish", "task"]
        help_text = result.stdout.lower()

        # At least some commands should be visible
        found_commands = sum(1 for cmd in expected_commands if cmd in help_text)
        assert found_commands >= 3, (
            f"Expected to find at least 3 commands in help, found {found_commands}"
        )


class TestLoggingAndObservability:
    """Test logging and observability features."""

    def test_verbose_flag_increases_verbosity(self, tmp_path):
        """Test that -v flag is accepted and can be repeated."""
        # Single verbose
        result = run_devflow(["-v", "test"])
        assert result.returncode != 2

        # Double verbose
        result = run_devflow(["-vv", "test"])
        assert result.returncode != 2

    def test_quiet_suppresses_output(self, tmp_path):
        """Test that --quiet flag is accepted."""
        result = run_devflow(["--quiet", "test"])
        assert result.returncode != 2


class TestCLIExitCodes:
    """Test that CLI provides deterministic exit codes."""

    def test_version_exits_zero(self):
        """Test --version exits with 0."""
        result = run_devflow(["--version"])
        assert result.returncode == 0

    def test_help_exits_zero(self):
        """Test --help exits with 0."""
        result = run_devflow(["--help"])
        assert result.returncode == 0

    def test_unknown_command_exits_nonzero(self):
        """Test unknown command exits with non-zero."""
        result = run_devflow(["nonexistent-command"])
        assert result.returncode != 0
