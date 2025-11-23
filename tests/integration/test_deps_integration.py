"""Integration tests for deps commands."""

import pytest

from devflow.app import AppContext
from devflow.commands.deps import DepsFreezeCommand, DepsSyncCommand
from devflow.commands.venv import VenvInitCommand


@pytest.fixture
def test_project_with_venv(tmp_path):
    """Create a test project with venv."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    # Create pyproject.toml
    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
default_python = "python3"

[tool.devflow.deps]
requirements = "requirements.txt"
freeze_output = "requirements-freeze.txt"
""")

    # Create a requirements.txt with a simple package
    requirements = project_root / "requirements.txt"
    requirements.write_text("wheel\n")

    # Create venv
    app_ctx = AppContext.create(
        project_root=project_root,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    venv_cmd = VenvInitCommand(app_ctx)
    venv_cmd.run()

    return project_root


def test_deps_sync_installs_packages(test_project_with_venv):
    """Test that deps sync installs packages."""
    app_ctx = AppContext.create(
        project_root=test_project_with_venv,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = DepsSyncCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 0


def test_deps_sync_no_venv_fails(tmp_path):
    """Test that deps sync fails if venv doesn't exist."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
""")

    app_ctx = AppContext.create(
        project_root=project_root,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = DepsSyncCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 1


def test_deps_sync_dry_run(test_project_with_venv):
    """Test that dry-run mode doesn't install packages."""
    app_ctx = AppContext.create(
        project_root=test_project_with_venv,
        dry_run=True,
        verbosity=0,
        quiet=True,
    )

    cmd = DepsSyncCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 0


def test_deps_freeze_creates_file(test_project_with_venv):
    """Test that deps freeze creates a freeze file."""
    # First sync to install some packages
    app_ctx = AppContext.create(
        project_root=test_project_with_venv,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    sync_cmd = DepsSyncCommand(app_ctx)
    sync_cmd.run()

    # Now freeze
    freeze_cmd = DepsFreezeCommand(app_ctx)
    exit_code = freeze_cmd.run()

    assert exit_code == 0

    freeze_file = test_project_with_venv / "requirements-freeze.txt"
    assert freeze_file.exists()

    # Check that file has content
    content = freeze_file.read_text()
    assert len(content) > 0

    # Check that it's sorted (deterministic)
    lines = [line for line in content.strip().split("\n") if line]
    assert lines == sorted(lines)


def test_deps_freeze_no_venv_fails(tmp_path):
    """Test that deps freeze fails if venv doesn't exist."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
""")

    app_ctx = AppContext.create(
        project_root=project_root,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    cmd = DepsFreezeCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 1


def test_deps_freeze_dry_run(test_project_with_venv):
    """Test that dry-run mode doesn't create freeze file."""
    app_ctx = AppContext.create(
        project_root=test_project_with_venv,
        dry_run=True,
        verbosity=0,
        quiet=True,
    )

    cmd = DepsFreezeCommand(app_ctx)
    exit_code = cmd.run()

    assert exit_code == 0

    freeze_file = test_project_with_venv / "requirements-freeze.txt"
    # Should not create the file in dry-run
    assert not freeze_file.exists()


def test_deps_sync_no_requirements_warns(tmp_path):
    """Test that sync warns when no requirements files exist."""
    project_root = tmp_path / "test_project"
    project_root.mkdir()

    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
""")

    # Create venv but no requirements.txt
    app_ctx = AppContext.create(
        project_root=project_root,
        dry_run=False,
        verbosity=0,
        quiet=True,
    )

    venv_cmd = VenvInitCommand(app_ctx)
    venv_cmd.run()

    # Try to sync
    cmd = DepsSyncCommand(app_ctx)
    exit_code = cmd.run()

    # Should succeed but warn
    assert exit_code == 0
