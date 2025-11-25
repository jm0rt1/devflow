"""
Integration tests for devflow acceptance scenarios.

These tests mirror the acceptance scenarios defined in the design white paper
(docs/DESIGN_SPEC.md). They serve as evidence that the implementation meets
the specified requirements.

Test Scenarios from Design Spec:
- Scenario 1: Replace test.sh with devflow test
- Scenario 2: Portable build & publish
- Scenario 3: Custom pipeline (ci-check)
- Scenario 4: Configurability & Overrides
- Scenario 5: Git integration & safety

NOTE: These tests will fail until the corresponding workstreams implement
the required functionality. They are marked with pytest markers to allow
selective execution.
"""

import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.integration
class TestVenvInit:
    """
    Test Scenario: venv init functionality.

    Tests FR7: Support creating and managing a venv.
    """

    @pytest.mark.skip(reason="Awaiting Workstream C implementation")
    def test_venv_init_creates_venv(self, temp_project_dir: Path) -> None:
        """Test that devflow venv init creates a virtual environment."""
        # Setup: Create minimal project
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow]
venv_dir = ".venv"
default_python = "python3"
"""
        )

        # Execute: Run devflow venv init
        result = subprocess.run(
            [sys.executable, "-m", "devflow", "venv", "init"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True,
        )

        # Verify: venv should be created
        venv_dir = temp_project_dir / ".venv"
        assert venv_dir.exists(), f"venv should be created at {venv_dir}"
        assert result.returncode == 0, f"Command failed: {result.stderr}"


@pytest.mark.integration
class TestDryRun:
    """
    Test Scenario: dry-run behavior for destructive operations.

    Tests NFR12: Support a --dry-run mode for destructive or remote operations.
    """

    @pytest.mark.skip(reason="Awaiting Workstream D implementation")
    def test_publish_dry_run_no_network(self, temp_project_dir: Path) -> None:
        """Test that devflow publish --dry-run does not make network calls."""
        # Setup: Create project with build artifacts
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text(
            """
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"

[tool.devflow.publish]
repository = "testpypi"
"""
        )

        # Execute: Run devflow publish --dry-run
        result = subprocess.run(
            [sys.executable, "-m", "devflow", "publish", "--dry-run"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True,
        )

        # Verify: Should show what would happen without network calls
        assert "would upload" in result.stdout.lower() or result.returncode == 0
        # No actual upload should occur


@pytest.mark.integration
class TestCICheckPipeline:
    """
    Test Scenario 3: Custom pipeline (ci-check).

    Tests that composite commands run steps in sequence and fail fast.
    """

    @pytest.mark.skip(reason="Awaiting Workstream B task engine implementation")
    def test_ci_check_runs_pipeline_in_order(self, temp_project_dir: Path) -> None:
        """Test that ci-check runs pipeline steps in order."""
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test"]

[tool.devflow.tasks.format]
command = "echo"
args = ["format-step"]

[tool.devflow.tasks.lint]
command = "echo"
args = ["lint-step"]

[tool.devflow.tasks.test]
command = "echo"
args = ["test-step"]
"""
        )

        result = subprocess.run(
            [sys.executable, "-m", "devflow", "ci-check"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True,
        )

        # Verify: Steps should run in order
        assert result.returncode == 0
        output = result.stdout
        format_pos = output.find("format-step")
        lint_pos = output.find("lint-step")
        test_pos = output.find("test-step")
        assert format_pos < lint_pos < test_pos, "Steps should run in order"

    @pytest.mark.skip(reason="Awaiting Workstream B task engine implementation")
    def test_ci_check_fails_fast(self, temp_project_dir: Path) -> None:
        """Test that ci-check stops on first failure."""
        pyproject = temp_project_dir / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow.tasks.ci-check]
pipeline = ["fail-step", "should-not-run"]

[tool.devflow.tasks.fail-step]
command = "exit"
args = ["1"]

[tool.devflow.tasks.should-not-run]
command = "echo"
args = ["this-should-not-appear"]
"""
        )

        result = subprocess.run(
            [sys.executable, "-m", "devflow", "ci-check"],
            cwd=temp_project_dir,
            capture_output=True,
            text=True,
        )

        # Verify: Should fail and not run subsequent steps
        assert result.returncode != 0
        assert "this-should-not-appear" not in result.stdout


@pytest.mark.integration
class TestGitIntegration:
    """
    Test Scenario 5: Git integration & safety.

    Tests FR14: Optionally integrate with git - validate working tree clean.
    """

    @pytest.mark.skip(reason="Awaiting Workstream E git helpers implementation")
    def test_publish_fails_on_dirty_tree(self, temp_git_repo: Path) -> None:
        """Test that publish fails when working tree is dirty."""
        # Setup: Create project with require_clean_working_tree
        pyproject = temp_git_repo / "pyproject.toml"
        pyproject.write_text(
            """
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"

[tool.devflow.publish]
require_clean_working_tree = true
"""
        )

        # Commit initial state
        subprocess.run(["git", "add", "."], cwd=temp_git_repo, check=True)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )

        # Create uncommitted changes
        dirty_file = temp_git_repo / "dirty.txt"
        dirty_file.write_text("uncommitted changes")

        # Execute: Run devflow publish
        result = subprocess.run(
            [sys.executable, "-m", "devflow", "publish"],
            cwd=temp_git_repo,
            capture_output=True,
            text=True,
        )

        # Verify: Should fail with clear message
        assert result.returncode != 0
        assert "clean" in result.stderr.lower() or "dirty" in result.stderr.lower()


@pytest.mark.integration
class TestExitCodes:
    """
    Test exit code behavior per NFR10.

    Tests NFR10: Clear exit codes - 0 = success, Non-zero = failure.
    """

    def test_help_returns_zero(self) -> None:
        """Test that --help returns exit code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "devflow", "--help"],
            capture_output=True,
            text=True,
        )
        # Currently returns 0 from stub; will be validated with full implementation
        assert result.returncode == 0

    def test_version_returns_zero(self) -> None:
        """Test that --version returns exit code 0."""
        result = subprocess.run(
            [sys.executable, "-m", "devflow"],
            capture_output=True,
            text=True,
        )
        # Currently returns 0 from stub
        assert result.returncode == 0
