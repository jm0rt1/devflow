"""Tests for path utilities."""

"""Tests for project root detection."""

import tempfile
from pathlib import Path

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
def test_find_project_root_with_pyproject_toml():
    """Test finding project root with pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create pyproject.toml
        (root / "pyproject.toml").touch()
        # Create a subdirectory
        subdir = root / "src" / "package"
        subdir.mkdir(parents=True)

        # Should find root from subdirectory
        found_root = find_project_root(subdir)
        assert found_root == root


def test_find_project_root_with_devflow_toml():
    """Test finding project root with devflow.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create devflow.toml
        (root / "devflow.toml").touch()
        # Create a subdirectory
        subdir = root / "tests" / "unit"
        subdir.mkdir(parents=True)

        # Should find root from subdirectory
        found_root = find_project_root(subdir)
        assert found_root == root


def test_find_project_root_prefers_closest():
    """Test that find_project_root prefers the closest marker file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Create pyproject.toml at root
        (root / "pyproject.toml").touch()
        # Create nested project
        nested = root / "nested"
        nested.mkdir()
        (nested / "devflow.toml").touch()
        # Create deep subdirectory
        subdir = nested / "src"
        subdir.mkdir()

        # Should find nested root, not outer root
        found_root = find_project_root(subdir)
        assert found_root == nested


def test_find_project_root_no_marker_raises():
    """Test that find_project_root raises when no marker file found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        subdir = root / "some" / "deep" / "path"
        subdir.mkdir(parents=True)

        # Should raise RuntimeError
        with pytest.raises(RuntimeError, match="Project root not found"):
            find_project_root(subdir)


def test_find_project_root_uses_cwd_when_none():
    """Test that find_project_root uses cwd when start is None."""
    # This test relies on the test being run from a directory with pyproject.toml
    # Since we're in the devflow project root, it should work
    found_root = find_project_root(None)
    assert (found_root / "pyproject.toml").exists()
