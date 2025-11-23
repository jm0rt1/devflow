"""Unit tests for path utilities."""

import os
from pathlib import Path

import pytest

from devflow.core.paths import find_project_root, get_venv_executable, get_venv_python


def test_find_project_root_with_pyproject(tmp_path: Path):
    """Test finding project root with pyproject.toml."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("")

    subdir = project_dir / "subdir" / "nested"
    subdir.mkdir(parents=True)

    root = find_project_root(subdir)

    assert root == project_dir


def test_find_project_root_with_devflow_toml(tmp_path: Path):
    """Test finding project root with devflow.toml."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "devflow.toml").write_text("")

    subdir = project_dir / "subdir"
    subdir.mkdir()

    root = find_project_root(subdir)

    assert root == project_dir


def test_find_project_root_not_found(tmp_path: Path):
    """Test that RuntimeError is raised when project root is not found."""
    with pytest.raises(RuntimeError, match="Project root not found"):
        find_project_root(tmp_path)


def test_get_venv_python_unix(tmp_path: Path, monkeypatch):
    """Test getting venv Python path on Unix."""
    monkeypatch.setattr(os, "name", "posix")

    venv_dir = tmp_path / ".venv"

    python_path = get_venv_python(venv_dir)

    assert python_path == venv_dir / "bin" / "python"


def test_get_venv_python_windows(tmp_path: Path, monkeypatch):
    """Test getting venv Python path on Windows."""
    monkeypatch.setattr(os, "name", "nt")

    venv_dir = tmp_path / ".venv"

    python_path = get_venv_python(venv_dir)

    assert python_path == venv_dir / "Scripts" / "python.exe"


def test_get_venv_executable_unix(tmp_path: Path, monkeypatch):
    """Test getting venv executable path on Unix."""
    monkeypatch.setattr(os, "name", "posix")

    venv_dir = tmp_path / ".venv"

    pytest_path = get_venv_executable(venv_dir, "pytest")

    assert pytest_path == venv_dir / "bin" / "pytest"


def test_get_venv_executable_windows(tmp_path: Path, monkeypatch):
    """Test getting venv executable path on Windows."""
    monkeypatch.setattr(os, "name", "nt")

    venv_dir = tmp_path / ".venv"

    # Test with .exe that exists
    exe_path = venv_dir / "Scripts" / "pytest.exe"
    exe_path.parent.mkdir(parents=True)
    exe_path.write_text("")

    pytest_path = get_venv_executable(venv_dir, "pytest")

    assert pytest_path == exe_path
