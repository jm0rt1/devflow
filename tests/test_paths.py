"""Tests for project root detection."""

import os
from pathlib import Path

import pytest

from devflow.core.paths import ProjectRootNotFoundError, find_project_root, resolve_path


class TestFindProjectRoot:
    """Tests for find_project_root function."""

    def test_finds_pyproject_toml(self, tmp_path: Path) -> None:
        """Should find project root when pyproject.toml exists."""
        # Create pyproject.toml
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        # Create a subdirectory
        subdir = tmp_path / "src" / "package"
        subdir.mkdir(parents=True)

        # Find root from subdirectory
        result = find_project_root(subdir)
        assert result == tmp_path

    def test_finds_devflow_toml(self, tmp_path: Path) -> None:
        """Should find project root when devflow.toml exists."""
        # Create devflow.toml
        (tmp_path / "devflow.toml").write_text("[devflow]\nvenv_dir = '.venv'\n")

        # Create a subdirectory
        subdir = tmp_path / "nested" / "deep" / "path"
        subdir.mkdir(parents=True)

        # Find root from subdirectory
        result = find_project_root(subdir)
        assert result == tmp_path

    def test_prefers_pyproject_over_devflow(self, tmp_path: Path) -> None:
        """Should find the first marker file when walking up."""
        # Create both files at root
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        (tmp_path / "devflow.toml").write_text("[devflow]\n")

        result = find_project_root(tmp_path)
        assert result == tmp_path

    def test_finds_closest_root_marker(self, tmp_path: Path) -> None:
        """Should find the closest root marker when nested projects exist."""
        # Create outer project
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'outer'\n")

        # Create inner project
        inner = tmp_path / "packages" / "inner"
        inner.mkdir(parents=True)
        (inner / "pyproject.toml").write_text("[project]\nname = 'inner'\n")

        # Find root from inner project
        result = find_project_root(inner)
        assert result == inner

        # Find root from outer should still work
        result = find_project_root(tmp_path)
        assert result == tmp_path

    def test_raises_when_no_marker_found(self, tmp_path: Path) -> None:
        """Should raise ProjectRootNotFoundError when no markers exist."""
        # Create a directory without any markers
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ProjectRootNotFoundError) as exc_info:
            find_project_root(empty_dir)

        assert "Project root not found" in str(exc_info.value)
        assert "pyproject.toml" in str(exc_info.value) or "devflow.toml" in str(exc_info.value)

    def test_uses_current_directory_when_none(self, tmp_path: Path) -> None:
        """Should use current directory when start is None."""
        # Create pyproject.toml in tmp_path
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        # Change to the directory
        original_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            result = find_project_root(None)
            assert result == tmp_path
        finally:
            os.chdir(original_cwd)

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        """Should always return an absolute path."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        result = find_project_root(tmp_path)
        assert result.is_absolute()


class TestResolvePath:
    """Tests for resolve_path function."""

    def test_resolves_relative_path(self, tmp_path: Path) -> None:
        """Should resolve relative path against base."""
        result = resolve_path(tmp_path, "src/package")
        assert result == (tmp_path / "src" / "package").resolve()

    def test_resolves_dot_paths(self, tmp_path: Path) -> None:
        """Should handle . and .. in paths."""
        result = resolve_path(tmp_path, "./src/../tests")
        assert result == (tmp_path / "tests").resolve()

    def test_returns_absolute_path(self, tmp_path: Path) -> None:
        """Should always return an absolute path."""
        result = resolve_path(tmp_path, "relative")
        assert result.is_absolute()
