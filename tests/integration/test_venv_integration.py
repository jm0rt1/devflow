"""Integration tests for venv commands."""

import sys

import pytest

from devflow.app import AppContext
from devflow.commands.venv import VenvInitCommand


@pytest.fixture
def test_project(tmp_path):
    """Create a test project with pyproject.toml."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create a minimal pyproject.toml
    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
default_python = "python3"
""")

    return project_root


def test_venv_init_creates_venv(test_project):
    """Test that venv init creates a virtual environment."""
    app_ctx = AppContext.create(
        project_root=test_project,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = VenvInitCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 0

    venv_dir = test_project / ".venv"
    assert venv_dir.exists()
    assert venv_dir.is_dir()

    # Check that Python executable exists
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"

    assert python_path.exists()


def test_venv_init_idempotent(test_project):
    """Test that running venv init twice doesn't fail."""
    app_ctx = AppContext.create(
        project_root=test_project,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = VenvInitCommand(app_ctx)

    # Run once
    exit_code1 = cmd.run()
    assert exit_code1 == 0

    # Run again
    exit_code2 = cmd.run()
    assert exit_code2 == 0

    venv_dir = test_project / ".venv"
    assert venv_dir.exists()


def test_venv_init_recreate(test_project):
    """Test that --recreate flag recreates the venv."""
    app_ctx = AppContext.create(
        project_root=test_project,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = VenvInitCommand(app_ctx)

    # Create initial venv
    exit_code = cmd.run()
    assert exit_code == 0

    venv_dir = test_project / ".venv"

    # Create a marker file
    marker = venv_dir / "marker.txt"
    marker.write_text("test")
    assert marker.exists()

    # Recreate venv
    exit_code = cmd.run(recreate=True)
    assert exit_code == 0

    # Marker should be gone
    assert not marker.exists()
    # But venv should still exist
    assert venv_dir.exists()


def test_venv_init_dry_run(test_project):
    """Test that dry-run mode doesn't create the venv."""
    app_ctx = AppContext.create(
        project_root=test_project,
        dry_run=True,
        verbosity=0,
        quiet=True,
    )

    cmd = VenvInitCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 0

    venv_dir = test_project / ".venv"
    # Should not actually create the venv
    assert not venv_dir.exists()


def test_venv_init_custom_python(test_project):
    """Test specifying custom Python executable."""
    # This test assumes python3 is available
    app_ctx = AppContext.create(
        project_root=test_project,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = VenvInitCommand(app_ctx)
    exit_code = cmd.run(python="python3")

    assert exit_code == 0

    venv_dir = test_project / ".venv"
    assert venv_dir.exists()
