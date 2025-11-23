"""Integration tests for the build command."""

from pathlib import Path

from devflow.app import AppContext
from devflow.commands.build import build_command


def test_build_command_requires_venv(temp_project: Path):
    """Test that build command requires a venv to exist."""
    app = AppContext(project_root=temp_project, quiet=True)

    result = build_command(app)

    assert result == 1


def test_build_command_creates_dist(venv_project: Path):
    """Test that build command creates distribution artifacts."""
    app = AppContext(project_root=venv_project, quiet=True)

    result = build_command(app)

    assert result == 0

    # Check that dist directory was created with artifacts
    dist_dir = venv_project / "dist"
    assert dist_dir.exists()

    # Should have wheel and sdist
    artifacts = list(dist_dir.glob("*"))
    assert len(artifacts) >= 1  # At least one artifact


def test_build_command_cleans_dist(venv_project: Path):
    """Test that build command cleans dist directory before building."""
    # Create dist directory with old files
    dist_dir = venv_project / "dist"
    dist_dir.mkdir(exist_ok=True)
    old_file = dist_dir / "old_file.txt"
    old_file.write_text("old content")

    app = AppContext(project_root=venv_project, quiet=True)

    result = build_command(app, clean=True)

    assert result == 0

    # Old file should be gone
    assert not old_file.exists()


def test_build_command_no_clean(venv_project: Path):
    """Test that build command can skip cleaning dist directory."""
    # Create dist directory with old files
    dist_dir = venv_project / "dist"
    dist_dir.mkdir(exist_ok=True)
    old_file = dist_dir / "old_file.txt"
    old_file.write_text("old content")

    app = AppContext(project_root=venv_project, quiet=True)

    result = build_command(app, clean=False)

    assert result == 0

    # Old file should still exist
    assert old_file.exists()


def test_build_command_dry_run(venv_project: Path):
    """Test that build command respects dry-run mode."""
    app = AppContext(project_root=venv_project, dry_run=True, verbosity=1)

    result = build_command(app)

    # Dry run always succeeds
    assert result == 0

    # Dist directory should not be created in dry-run
    dist_dir = venv_project / "dist"
    assert not dist_dir.exists()
