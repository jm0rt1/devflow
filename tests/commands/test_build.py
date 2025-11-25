"""Integration tests for the build command.

Tests the devflow build command including:
- Happy path execution
- Dist directory cleanup behavior
- Configurable backend
- Dry-run behavior
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from devflow.commands.build import (
    BuildConfig,
    build_build_command,
    clean_dist_directory,
    get_build_config,
    run_build,
)


@dataclass
class MockPathsConfig:
    """Mock paths configuration."""

    dist_dir: str = "dist"


@dataclass
class MockConfig:
    """Mock configuration for testing."""

    build_backend: str = "build"
    paths: MockPathsConfig = field(default_factory=MockPathsConfig)
    tasks: dict[str, Any] = field(default_factory=dict)


@dataclass
class MockAppContext:
    """Mock application context for testing."""

    project_root: Path = Path("/tmp/test-project")
    config: Any = field(default_factory=MockConfig)
    dry_run: bool = False
    verbose: int = 0
    quiet: bool = False
    _venv_python: Path | None = None

    def get_venv_python(self) -> Path | None:
        return self._venv_python


class TestGetBuildConfig:
    """Tests for get_build_config function."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = MockConfig()
        build_config = get_build_config(config)

        assert build_config.backend == "build"
        assert build_config.args == []
        assert build_config.use_venv is True
        assert build_config.clean_dist is True
        assert build_config.dist_dir == "dist"

    def test_custom_backend(self) -> None:
        """Test custom build backend from config."""
        config = MockConfig(build_backend="hatchling")
        build_config = get_build_config(config)

        assert build_config.backend == "hatchling"

    def test_paths_dist_dir(self) -> None:
        """Test custom dist directory from paths config."""
        config = MockConfig(paths=MockPathsConfig(dist_dir="build/dist"))
        build_config = get_build_config(config)

        assert build_config.dist_dir == "build/dist"

    def test_task_config_override(self) -> None:
        """Test task-specific configuration overrides."""
        config = MockConfig(
            build_backend="build",
            tasks={
                "build": {
                    "backend": "poetry-build",
                    "args": ["--format", "wheel"],
                    "clean_dist": False,
                    "use_venv": False,
                }
            },
        )
        build_config = get_build_config(config)

        assert build_config.backend == "poetry-build"
        assert build_config.args == ["--format", "wheel"]
        assert build_config.clean_dist is False
        assert build_config.use_venv is False


class TestBuildBuildCommand:
    """Tests for build_build_command function."""

    def test_default_build_command(self) -> None:
        """Test default python -m build command."""
        config = BuildConfig()
        cmd = build_build_command(config)

        assert cmd == ["python", "-m", "build"]

    def test_hatchling_command(self) -> None:
        """Test hatchling build command."""
        config = BuildConfig(backend="hatchling")
        cmd = build_build_command(config)

        assert cmd == ["python", "-m", "hatchling", "build"]

    def test_poetry_build_command(self) -> None:
        """Test poetry build command."""
        config = BuildConfig(backend="poetry-build")
        cmd = build_build_command(config)

        assert cmd == ["poetry", "build"]

    def test_flit_command(self) -> None:
        """Test flit build command."""
        config = BuildConfig(backend="flit")
        cmd = build_build_command(config)

        assert cmd == ["python", "-m", "flit", "build"]

    def test_custom_backend(self) -> None:
        """Test custom backend command."""
        config = BuildConfig(backend="custom_builder")
        cmd = build_build_command(config)

        assert cmd == ["python", "-m", "custom_builder"]

    def test_with_args(self) -> None:
        """Test command with additional args."""
        config = BuildConfig(args=["--no-isolation"])
        cmd = build_build_command(config)

        assert cmd == ["python", "-m", "build", "--no-isolation"]

    def test_custom_python_path(self) -> None:
        """Test command with custom python path."""
        config = BuildConfig()
        cmd = build_build_command(config, python_path="/usr/local/bin/python3.11")

        assert cmd == ["/usr/local/bin/python3.11", "-m", "build"]


class TestCleanDistDirectory:
    """Tests for clean_dist_directory function."""

    def test_nonexistent_directory(self, tmp_path: Path) -> None:
        """Test cleaning nonexistent directory returns True."""
        result = clean_dist_directory(tmp_path, "dist", dry_run=False, verbose=0)
        assert result is True

    def test_dry_run_does_not_delete(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't delete directory."""
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        (dist_path / "test.whl").touch()

        result = clean_dist_directory(tmp_path, "dist", dry_run=True, verbose=1)

        assert result is True
        assert dist_path.exists()
        assert (dist_path / "test.whl").exists()

    def test_clean_existing_directory(self, tmp_path: Path) -> None:
        """Test cleaning existing directory."""
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        (dist_path / "old.whl").touch()
        (dist_path / "old.tar.gz").touch()

        result = clean_dist_directory(tmp_path, "dist", dry_run=False, verbose=0)

        assert result is True
        assert not dist_path.exists()


class TestRunBuild:
    """Tests for run_build function."""

    def test_dry_run_mode(self) -> None:
        """Test that dry-run mode doesn't execute commands."""
        app = MockAppContext(dry_run=True, verbose=1)

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            result = run_build(app)

            mock_run.assert_not_called()
            assert result == 0

    def test_successful_build(self, tmp_path: Path) -> None:
        """Test successful build execution."""
        # Create a mock dist directory that appears after build
        dist_path = tmp_path / "dist"

        app = MockAppContext(project_root=tmp_path)

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            # Simulate successful build
            def create_dist(*args: Any, **kwargs: Any) -> MagicMock:
                dist_path.mkdir(exist_ok=True)
                (dist_path / "package-1.0.0-py3-none-any.whl").touch()
                return MagicMock(returncode=0)

            mock_run.side_effect = create_dist
            result = run_build(app)

            mock_run.assert_called_once()
            assert result == 0

    def test_failing_build(self) -> None:
        """Test failed build returns correct exit code."""
        app = MockAppContext()

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = run_build(app)

            assert result == 1

    def test_no_clean_flag(self, tmp_path: Path) -> None:
        """Test --no-clean skips dist directory cleaning."""
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        old_file = dist_path / "old.whl"
        old_file.touch()

        app = MockAppContext(project_root=tmp_path)

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            run_build(app, no_clean=True)

            # Old file should still exist (not cleaned)
            assert old_file.exists()

    def test_clean_dist_before_build(self, tmp_path: Path) -> None:
        """Test dist directory is cleaned before build by default."""
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        old_file = dist_path / "old.whl"
        old_file.touch()

        app = MockAppContext(project_root=tmp_path)

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            run_build(app, no_clean=False)

            # Old file should be gone (cleaned)
            assert not old_file.exists()

    def test_venv_enforcement(self, tmp_path: Path) -> None:
        """Test that build uses venv python when configured."""
        venv_python = Path("/tmp/test-venv/bin/python")
        app = MockAppContext(project_root=tmp_path, _venv_python=venv_python)

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Mock venv_python.exists() to return True
            with patch.object(Path, "exists", return_value=True):
                run_build(app, no_clean=True)

            # Check that the command uses venv python
            call_args = mock_run.call_args
            assert call_args is not None, "subprocess.run was not called"
            cmd = call_args[0][0]
            assert str(venv_python) in cmd[0]

    def test_build_tool_not_found(self) -> None:
        """Test handling of missing build tool."""
        app = MockAppContext()

        with patch("devflow.commands.build.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("build not found")
            result = run_build(app)

            assert result == 1
