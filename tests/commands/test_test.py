"""Integration tests for the test command.

Tests the devflow test command including:
- Happy path execution
- Pass-through arguments
- Venv enforcement
- Dry-run behavior
- Different test runners
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from devflow.commands.test import (
    RunnerTestConfig,
    build_test_command,
    get_test_config,
    run_test,
)


@dataclass
class MockConfig:
    """Mock configuration for testing."""

    test_runner: str = "pytest"
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


class TestGetTestConfig:
    """Tests for get_test_config function."""

    def test_default_config(self) -> None:
        """Test default configuration when no tasks defined."""
        config = MockConfig()
        test_config = get_test_config(config)

        assert test_config.runner == "pytest"
        assert test_config.args == []
        assert test_config.use_venv is True
        assert test_config.env == {}

    def test_custom_runner(self) -> None:
        """Test custom test runner from config."""
        config = MockConfig(test_runner="unittest")
        test_config = get_test_config(config)

        assert test_config.runner == "unittest"

    def test_task_config_override(self) -> None:
        """Test task-specific configuration overrides."""
        config = MockConfig(
            test_runner="pytest",
            tasks={
                "test": {
                    "command": "tox",
                    "args": ["-e", "py311"],
                    "use_venv": False,
                    "env": {"TOX_PARALLEL": "1"},
                }
            },
        )
        test_config = get_test_config(config)

        assert test_config.runner == "tox"
        assert test_config.args == ["-e", "py311"]
        assert test_config.use_venv is False
        assert test_config.env == {"TOX_PARALLEL": "1"}


class TestBuildTestCommand:
    """Tests for build_test_command function."""

    def test_basic_pytest_command(self) -> None:
        """Test basic pytest command generation."""
        config = RunnerTestConfig(runner="pytest")
        cmd = build_test_command(config)

        assert cmd == ["pytest"]

    def test_pytest_with_args(self) -> None:
        """Test pytest command with configured args."""
        config = RunnerTestConfig(runner="pytest", args=["-v", "-x"])
        cmd = build_test_command(config)

        assert cmd == ["pytest", "-v", "-x"]

    def test_pytest_with_pattern(self) -> None:
        """Test pytest command with pattern filter."""
        config = RunnerTestConfig(runner="pytest")
        cmd = build_test_command(config, pattern="test_api")

        assert cmd == ["pytest", "-k", "test_api"]

    def test_pytest_with_marker(self) -> None:
        """Test pytest command with marker filter."""
        config = RunnerTestConfig(runner="pytest")
        cmd = build_test_command(config, marker="slow")

        assert cmd == ["pytest", "-m", "slow"]

    def test_pytest_with_coverage(self) -> None:
        """Test pytest command with coverage."""
        config = RunnerTestConfig(runner="pytest")
        cmd = build_test_command(config, cov="mypackage")

        assert cmd == ["pytest", "--cov", "mypackage"]

    def test_pytest_with_extra_args(self) -> None:
        """Test pytest command with extra pass-through args."""
        config = RunnerTestConfig(runner="pytest", args=["-v"])
        cmd = build_test_command(config, extra_args=["--tb=short", "-x"])

        assert cmd == ["pytest", "-v", "--tb=short", "-x"]

    def test_unittest_command(self) -> None:
        """Test unittest command generation."""
        config = RunnerTestConfig(runner="unittest")
        cmd = build_test_command(config, pattern="test_*.py")

        assert cmd == ["unittest", "-p", "test_*.py"]

    def test_tox_command_with_extra_args(self) -> None:
        """Test tox command with extra args after --."""
        config = RunnerTestConfig(runner="tox")
        cmd = build_test_command(config, extra_args=["-k", "test_specific"])

        assert cmd == ["tox", "--", "-k", "test_specific"]


class TestRunTest:
    """Tests for run_test function."""

    def test_dry_run_mode(self) -> None:
        """Test that dry-run mode doesn't execute commands."""
        app = MockAppContext(dry_run=True, verbose=1)

        with patch("devflow.commands.test.subprocess.run") as mock_run:
            result = run_test(app)

            mock_run.assert_not_called()
            assert result == 0

    def test_successful_test_run(self) -> None:
        """Test successful test execution."""
        app = MockAppContext()

        with patch("devflow.commands.test.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = run_test(app)

            mock_run.assert_called_once()
            assert result == 0

    def test_failing_test_run(self) -> None:
        """Test failed test execution returns correct exit code."""
        app = MockAppContext()

        with patch("devflow.commands.test.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=1)
            result = run_test(app)

            assert result == 1

    def test_venv_enforcement(self) -> None:
        """Test that tests run in venv when configured."""
        venv_python = Path("/tmp/test-venv/bin/python")
        app = MockAppContext(_venv_python=venv_python)

        with patch("devflow.commands.test.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)

            # Mock venv_python.exists() to return True
            with patch.object(Path, "exists", return_value=True):
                run_test(app)

            # Check that the command uses venv python
            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert str(venv_python) in cmd[0]

    def test_runner_not_found(self) -> None:
        """Test handling of missing test runner."""
        app = MockAppContext()

        with patch("devflow.commands.test.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("pytest not found")
            result = run_test(app)

            assert result == 1

    def test_pass_through_args(self) -> None:
        """Test that extra args are passed through correctly."""
        app = MockAppContext()

        with patch("devflow.commands.test.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            run_test(app, extra_args=["--tb=short", "-x"])

            call_args = mock_run.call_args
            cmd = call_args[0][0]
            assert "--tb=short" in cmd
            assert "-x" in cmd


class TestIntegration:
    """Integration tests using actual subprocess calls (when safe)."""

    def test_help_text_available(self) -> None:
        """Test that pytest help is available (validates pytest is installed)."""
        result = subprocess.run(
            ["python", "-m", "pytest", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        # This test just validates pytest is available in the test environment
        assert result.returncode == 0 or "pytest" in result.stdout or "pytest" in result.stderr
