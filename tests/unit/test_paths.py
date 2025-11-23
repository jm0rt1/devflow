"""Tests for project root detection."""

import tempfile
from pathlib import Path

import pytest

from devflow.core.paths import find_project_root


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
