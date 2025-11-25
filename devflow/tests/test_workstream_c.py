"""Integration tests for Workstream C: Venv & Dependency Management.

These tests validate venv creation, dependency sync, freeze output,
and path resolution on Linux/macOS/WSL Git Bash where feasible.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from devflow.commands.deps import DepsManager, create_deps_manager
from devflow.commands.venv import VenvManager, create_venv_manager
from devflow.core.paths import (
    build_venv_command,
    find_project_root,
    get_venv_bin_dir,
    get_venv_dir,
    get_venv_env,
    get_venv_pip,
    get_venv_python,
    has_pyproject_dependencies,
    is_venv_active,
    resolve_requirements_files,
    venv_exists,
)


class TestPathHelpers:
    """Tests for core/paths.py path utilities."""

    def test_find_project_root_with_pyproject(self, tmp_path: Path) -> None:
        """Test finding project root with pyproject.toml."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)

        root = find_project_root(subdir)
        assert root == tmp_path

    def test_find_project_root_with_devflow_toml(self, tmp_path: Path) -> None:
        """Test finding project root with devflow.toml."""
        (tmp_path / "devflow.toml").write_text("[devflow]\nvenv_dir = '.venv'\n")
        subdir = tmp_path / "src"
        subdir.mkdir()

        root = find_project_root(subdir)
        assert root == tmp_path

    def test_find_project_root_not_found(self, tmp_path: Path) -> None:
        """Test error when project root is not found."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(RuntimeError, match="Project root not found"):
            find_project_root(empty_dir)

    def test_get_venv_dir(self, tmp_path: Path) -> None:
        """Test getting venv directory path."""
        venv_path = get_venv_dir(tmp_path, ".venv")
        assert venv_path == (tmp_path / ".venv").resolve()

        custom_path = get_venv_dir(tmp_path, "my_env")
        assert custom_path == (tmp_path / "my_env").resolve()

    def test_get_venv_python_unix(self, tmp_path: Path) -> None:
        """Test getting venv Python path on Unix."""
        venv_dir = tmp_path / ".venv"
        python_path = get_venv_python(venv_dir)

        if sys.platform == "win32":
            assert python_path == venv_dir / "Scripts" / "python.exe"
        else:
            assert python_path == venv_dir / "bin" / "python"

    def test_get_venv_pip(self, tmp_path: Path) -> None:
        """Test getting venv pip path."""
        venv_dir = tmp_path / ".venv"
        pip_path = get_venv_pip(venv_dir)

        if sys.platform == "win32":
            assert pip_path == venv_dir / "Scripts" / "pip.exe"
        else:
            assert pip_path == venv_dir / "bin" / "pip"

    def test_get_venv_bin_dir(self, tmp_path: Path) -> None:
        """Test getting venv bin directory."""
        venv_dir = tmp_path / ".venv"
        bin_dir = get_venv_bin_dir(venv_dir)

        if sys.platform == "win32":
            assert bin_dir == venv_dir / "Scripts"
        else:
            assert bin_dir == venv_dir / "bin"

    def test_venv_exists_false(self, tmp_path: Path) -> None:
        """Test venv_exists returns False for non-existent venv."""
        venv_dir = tmp_path / ".venv"
        assert not venv_exists(venv_dir)

    def test_is_venv_active_false(self, tmp_path: Path) -> None:
        """Test is_venv_active returns False when not active."""
        venv_dir = tmp_path / ".venv"
        assert not is_venv_active(venv_dir)

    def test_get_venv_env(self, tmp_path: Path) -> None:
        """Test getting venv environment variables."""
        venv_dir = tmp_path / ".venv"
        env = get_venv_env(venv_dir)

        assert env["VIRTUAL_ENV"] == str(venv_dir.resolve())
        assert str(get_venv_bin_dir(venv_dir)) in env["PATH"]
        assert "PYTHONHOME" not in env

    def test_get_venv_env_with_extra(self, tmp_path: Path) -> None:
        """Test getting venv env with extra variables."""
        venv_dir = tmp_path / ".venv"
        extra = {"MY_VAR": "my_value"}
        env = get_venv_env(venv_dir, extra_env=extra)

        assert env["MY_VAR"] == "my_value"
        assert env["VIRTUAL_ENV"] == str(venv_dir.resolve())

    def test_resolve_requirements_files(self, tmp_path: Path) -> None:
        """Test resolving requirements files."""
        (tmp_path / "requirements.txt").write_text("requests\n")
        (tmp_path / "requirements-dev.txt").write_text("pytest\n")

        files = resolve_requirements_files(tmp_path)
        assert len(files) == 2
        assert tmp_path / "requirements.txt" in files
        assert tmp_path / "requirements-dev.txt" in files

    def test_resolve_requirements_files_no_dev(self, tmp_path: Path) -> None:
        """Test resolving requirements files without dev."""
        (tmp_path / "requirements.txt").write_text("requests\n")
        (tmp_path / "requirements-dev.txt").write_text("pytest\n")

        files = resolve_requirements_files(tmp_path, include_dev=False)
        assert len(files) == 1
        assert tmp_path / "requirements.txt" in files

    def test_resolve_requirements_files_custom(self, tmp_path: Path) -> None:
        """Test resolving custom requirements files."""
        (tmp_path / "deps.txt").write_text("requests\n")
        (tmp_path / "deps-dev.txt").write_text("pytest\n")

        files = resolve_requirements_files(
            tmp_path,
            requirements="deps.txt",
            dev_requirements="deps-dev.txt",
        )
        assert len(files) == 2
        assert tmp_path / "deps.txt" in files
        assert tmp_path / "deps-dev.txt" in files

    def test_resolve_requirements_files_missing(self, tmp_path: Path) -> None:
        """Test resolving when no requirements files exist."""
        files = resolve_requirements_files(tmp_path)
        assert len(files) == 0

    def test_has_pyproject_dependencies_true(self, tmp_path: Path) -> None:
        """Test detecting pyproject.toml with dependencies."""
        pyproject_content = """
[project]
name = "test"
dependencies = ["requests"]
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        assert has_pyproject_dependencies(tmp_path)

    def test_has_pyproject_dependencies_false(self, tmp_path: Path) -> None:
        """Test detecting pyproject.toml without dependencies."""
        pyproject_content = """
[project]
name = "test"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        assert not has_pyproject_dependencies(tmp_path)

    def test_has_pyproject_dependencies_no_file(self, tmp_path: Path) -> None:
        """Test when pyproject.toml doesn't exist."""
        assert not has_pyproject_dependencies(tmp_path)


class TestVenvManager:
    """Tests for VenvManager venv creation and management."""

    def test_venv_init_creates_venv(self, tmp_path: Path) -> None:
        """Test that venv init creates a virtual environment."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
            verbose=True,
        )

        result = manager.init()
        assert result == 0
        assert venv_exists(manager.venv_dir)
        assert get_venv_python(manager.venv_dir).exists()

    def test_venv_init_idempotent(self, tmp_path: Path) -> None:
        """Test that venv init is idempotent (doesn't recreate by default)."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )

        # First creation
        result1 = manager.init()
        assert result1 == 0

        # Get the creation time of a file in venv
        python_path = get_venv_python(manager.venv_dir)
        mtime1 = python_path.stat().st_mtime

        # Second call should not recreate
        result2 = manager.init()
        assert result2 == 0

        mtime2 = python_path.stat().st_mtime
        assert mtime1 == mtime2  # File not modified

    def test_venv_init_recreate(self, tmp_path: Path) -> None:
        """Test that venv init --recreate rebuilds the venv."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )

        # First creation
        result1 = manager.init()
        assert result1 == 0

        # Create a marker file
        marker = manager.venv_dir / "marker.txt"
        marker.write_text("test")
        assert marker.exists()

        # Recreate should remove the marker
        result2 = manager.init(recreate=True)
        assert result2 == 0
        assert not marker.exists()

    def test_venv_init_dry_run(self, tmp_path: Path) -> None:
        """Test that venv init --dry-run doesn't create venv."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
            dry_run=True,
        )

        result = manager.init()
        assert result == 0
        assert not venv_exists(manager.venv_dir)

    def test_venv_init_custom_venv_dir(self, tmp_path: Path) -> None:
        """Test venv init with custom venv directory name."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name="my_custom_venv",
        )

        result = manager.init()
        assert result == 0
        assert (tmp_path / "my_custom_venv").is_dir()
        assert venv_exists(manager.venv_dir)

    def test_venv_delete(self, tmp_path: Path) -> None:
        """Test that venv delete removes the venv."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )

        # Create venv
        manager.init()
        assert venv_exists(manager.venv_dir)

        # Delete venv
        result = manager.delete()
        assert result == 0
        assert not manager.venv_dir.exists()

    def test_venv_delete_nonexistent(self, tmp_path: Path) -> None:
        """Test that venv delete succeeds even if venv doesn't exist."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )

        result = manager.delete()
        assert result == 0

    def test_create_venv_manager_factory(self, tmp_path: Path) -> None:
        """Test the create_venv_manager factory function."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Change to tmp_path so find_project_root works
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            manager = create_venv_manager(venv_dir=".venv", verbose=True)
            assert manager.project_root == tmp_path.resolve()
            assert manager.venv_dir_name == ".venv"
            assert manager.verbose is True
        finally:
            os.chdir(original_cwd)


class TestDepsManager:
    """Tests for DepsManager dependency management."""

    @pytest.fixture
    def venv_project(self, tmp_path: Path):
        """Create a project with a virtual environment."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Create venv
        venv_manager = VenvManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )
        venv_manager.init()

        return tmp_path

    def test_deps_sync_no_venv(self, tmp_path: Path) -> None:
        """Test that deps sync fails when no venv exists."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        manager = DepsManager(
            project_root=tmp_path,
            venv_dir_name=".venv",
        )

        result = manager.sync()
        assert result == 1  # Should fail

    def test_deps_sync_from_requirements(self, venv_project: Path) -> None:
        """Test deps sync from requirements.txt."""
        # Create a simple requirements file with a standard package
        (venv_project / "requirements.txt").write_text("pip>=21.0\n")

        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
            verbose=True,
        )

        result = manager.sync()
        assert result == 0

    def test_deps_sync_dry_run(self, venv_project: Path) -> None:
        """Test deps sync dry run mode."""
        (venv_project / "requirements.txt").write_text("requests\n")

        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
            dry_run=True,
        )

        result = manager.sync()
        assert result == 0  # Should succeed without actually installing

    def test_deps_sync_no_requirements(self, venv_project: Path) -> None:
        """Test deps sync when no requirements files exist."""
        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
        )

        result = manager.sync()
        assert result == 0  # Should succeed with nothing to do

    def test_deps_freeze_basic(self, venv_project: Path) -> None:
        """Test deps freeze creates a freeze file."""
        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
            freeze_output="requirements-freeze.txt",
        )

        result = manager.freeze()
        assert result == 0

        freeze_file = venv_project / "requirements-freeze.txt"
        assert freeze_file.exists()

        content = freeze_file.read_text()
        assert "# This file is auto-generated by devflow deps freeze" in content

    def test_deps_freeze_deterministic_ordering(self, venv_project: Path) -> None:
        """Test that deps freeze output is deterministically ordered."""
        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
            freeze_output="requirements-freeze.txt",
        )

        # Freeze twice
        manager.freeze()
        content1 = (venv_project / "requirements-freeze.txt").read_text()

        manager.freeze()
        content2 = (venv_project / "requirements-freeze.txt").read_text()

        # Output should be identical
        assert content1 == content2

    def test_deps_freeze_dry_run(self, venv_project: Path) -> None:
        """Test deps freeze dry run mode."""
        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
            freeze_output="requirements-freeze.txt",
            dry_run=True,
        )

        result = manager.freeze()
        assert result == 0

        # File should not be created in dry run
        freeze_file = venv_project / "requirements-freeze.txt"
        assert not freeze_file.exists()

    def test_deps_freeze_custom_output(self, venv_project: Path) -> None:
        """Test deps freeze with custom output path."""
        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
            freeze_output="custom-freeze.txt",
        )

        result = manager.freeze()
        assert result == 0

        freeze_file = venv_project / "custom-freeze.txt"
        assert freeze_file.exists()

    def test_deps_list(self, venv_project: Path) -> None:
        """Test deps list command."""
        manager = DepsManager(
            project_root=venv_project,
            venv_dir_name=".venv",
        )

        result = manager.list()
        assert result == 0

    def test_create_deps_manager_factory(self, tmp_path: Path) -> None:
        """Test the create_deps_manager factory function."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            manager = create_deps_manager(
                venv_dir=".venv",
                freeze_output="freeze.txt",
                verbose=True,
            )
            assert manager.project_root == tmp_path.resolve()
            assert manager.venv_dir_name == ".venv"
            assert manager.freeze_output == "freeze.txt"
            assert manager.verbose is True
        finally:
            os.chdir(original_cwd)


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
        from devflow.core.paths import build_venv_command, get_venv_dir

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
        from devflow.core.paths import get_venv_dir, venv_exists, get_venv_python

        venv_dir = get_venv_dir(full_project, ".venv")

        # Other streams can check if venv exists
        assert venv_exists(venv_dir)

        # And get the python path
        python_path = get_venv_python(venv_dir)
        assert python_path.exists()
