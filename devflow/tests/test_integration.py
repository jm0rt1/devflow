"""Tests for the build_venv_command helper and cross-stream integration."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from devflow.commands.venv import VenvManager
from devflow.core.paths import (
    build_venv_command,
    get_venv_bin_dir,
    get_venv_dir,
    get_venv_python,
    venv_exists,
)


class TestBuildVenvCommand:
    """Tests for the build_venv_command helper."""

    @pytest.fixture
    def venv_project(self, tmp_path: Path):
        """Create a project with a virtual environment."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        venv_manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )
        venv_manager.init()

        return tmp_path

    def test_build_venv_command_no_venv(self, tmp_path: Path) -> None:
        """Test build_venv_command fails when venv doesn't exist."""
        venv_dir = tmp_path / ".venv"

        with pytest.raises(FileNotFoundError, match="Virtual environment not found"):
            build_venv_command(venv_dir, ["pytest", "-v"])

    def test_build_venv_command_use_venv_false(self, tmp_path: Path) -> None:
        """Test build_venv_command with use_venv=False."""
        venv_dir = tmp_path / ".venv"
        cmd, env = build_venv_command(venv_dir, ["pytest", "-v"], use_venv=False)

        assert cmd == ["pytest", "-v"]
        assert "VIRTUAL_ENV" not in env or env["VIRTUAL_ENV"] != str(venv_dir.resolve())

    def test_build_venv_command_python(self, venv_project: Path) -> None:
        """Test build_venv_command resolves python command."""
        venv_dir = venv_project / ".venv"
        cmd, env = build_venv_command(venv_dir, ["python", "-c", "print('hello')"])

        venv_python = get_venv_python(venv_dir)
        assert cmd[0] == str(venv_python)
        assert cmd[1:] == ["-c", "print('hello')"]
        assert env["VIRTUAL_ENV"] == str(venv_dir.resolve())

    def test_build_venv_command_pip(self, venv_project: Path) -> None:
        """Test build_venv_command resolves pip command."""
        venv_dir = venv_project / ".venv"
        cmd, env = build_venv_command(venv_dir, ["pip", "list"])

        # pip should be resolved to the venv pip
        assert "pip" in cmd[0]
        assert env["VIRTUAL_ENV"] == str(venv_dir.resolve())

    def test_build_venv_command_env_setup(self, venv_project: Path) -> None:
        """Test build_venv_command sets up correct environment."""
        venv_dir = venv_project / ".venv"
        cmd, env = build_venv_command(venv_dir, ["somecommand"])

        assert env["VIRTUAL_ENV"] == str(venv_dir.resolve())
        assert str(get_venv_bin_dir(venv_dir)) in env["PATH"]


class TestCrossStreamIntegration:
    """Tests simulating how other workstreams would use C's helpers."""

    @pytest.fixture
    def full_project(self, tmp_path: Path):
        """Create a complete project setup."""
        # Create pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Create requirements
        (tmp_path / "requirements.txt").write_text("# test requirements\n")

        # Create venv
        venv_manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )
        venv_manager.init()

        return tmp_path

    def test_other_stream_can_run_pytest(self, full_project: Path) -> None:
        """Test that other streams can use helpers to run pytest-like commands.

        This simulates how Workstream D (test/build/publish) would use our helpers.
        """
        venv_dir = get_venv_dir(full_project, ".venv")
        cmd, env = build_venv_command(venv_dir, ["python", "--version"])

        # Run the command
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        assert result.returncode == 0
        assert "Python" in result.stdout or "Python" in result.stderr

    def test_other_stream_can_check_venv_state(self, full_project: Path) -> None:
        """Test that other streams can check venv state.

        This simulates how any stream needing venv info would use our helpers.
        """
        venv_dir = get_venv_dir(full_project, ".venv")

        # Other streams can check if venv exists
        assert venv_exists(venv_dir)

        # And get the python path
        python_path = get_venv_python(venv_dir)
        assert python_path.exists()
