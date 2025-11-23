"""Tests for path utilities."""


import pytest

from devflow.core.paths import find_project_root


def test_find_project_root_with_pyproject_toml(tmp_path):
    """Test finding project root with pyproject.toml."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").touch()

    subdir = project / "src" / "mypackage"
    subdir.mkdir(parents=True)

    root = find_project_root(subdir)
    assert root == project


def test_find_project_root_with_devflow_toml(tmp_path):
    """Test finding project root with devflow.toml."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "devflow.toml").touch()

    subdir = project / "src"
    subdir.mkdir()

    root = find_project_root(subdir)
    assert root == project


def test_find_project_root_not_found(tmp_path):
    """Test error when project root not found."""
    subdir = tmp_path / "no-project"
    subdir.mkdir()

    with pytest.raises(RuntimeError) as exc_info:
        find_project_root(subdir)

    assert "Project root not found" in str(exc_info.value)


def test_find_project_root_uses_cwd_when_none(tmp_path, monkeypatch):
    """Test that find_project_root uses CWD when start is None."""
    project = tmp_path / "project"
    project.mkdir()
    (project / "pyproject.toml").touch()

    monkeypatch.chdir(project)

    root = find_project_root(None)
    assert root == project
