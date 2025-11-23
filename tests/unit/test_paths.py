"""Unit tests for path utilities."""

import pytest

from devflow.core.paths import find_project_root, get_venv_pip, get_venv_python


def test_find_project_root_with_pyproject(tmp_path):
    """Test finding project root with pyproject.toml."""
    # Create a project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "pyproject.toml").touch()

    subdir = project_root / "subdir"
    subdir.mkdir()

    # Should find root from subdir
    result = find_project_root(subdir)
    assert result == project_root


def test_find_project_root_with_devflow_toml(tmp_path):
    """Test finding project root with devflow.toml."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "devflow.toml").touch()

    # Should find root
    result = find_project_root(project_root)
    assert result == project_root


def test_find_project_root_not_found(tmp_path):
    """Test error when project root is not found."""
    with pytest.raises(RuntimeError, match="Project root not found"):
        find_project_root(tmp_path)


def test_get_venv_python_unix(tmp_path, monkeypatch):
    """Test getting Python path in Unix-like venv."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()

    bin_dir = venv_dir / "bin"
    bin_dir.mkdir()
    python_path = bin_dir / "python"
    python_path.touch()

    result = get_venv_python(venv_dir)
    assert result == python_path


def test_get_venv_python_not_found(tmp_path):
    """Test error when Python is not found in venv."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()

    with pytest.raises(RuntimeError, match="Python executable not found"):
        get_venv_python(venv_dir)


def test_get_venv_pip_unix(tmp_path):
    """Test getting pip path in Unix-like venv."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()

    bin_dir = venv_dir / "bin"
    bin_dir.mkdir()
    pip_path = bin_dir / "pip"
    pip_path.touch()

    result = get_venv_pip(venv_dir)
    assert result == pip_path
