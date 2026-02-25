"""Tests for VenvManager venv creation and management."""

from __future__ import annotations

import os
from pathlib import Path

from devflow.commands.venv import VenvManager, create_venv_manager
from devflow.core.paths import get_venv_python, venv_exists


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
