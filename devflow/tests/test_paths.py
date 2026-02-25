"""Tests for core/paths.py path utilities."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from devflow.core.paths import (
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
