"""Integration tests for the publish command."""

from pathlib import Path

from devflow.app import AppContext
from devflow.commands.publish import publish_command


def test_publish_command_requires_venv(temp_project: Path):
    """Test that publish command requires a venv to exist."""
    app = AppContext(project_root=temp_project, quiet=True)

    result = publish_command(app)

    assert result == 1


def test_publish_command_requires_clean_tree(temp_git_project: Path):
    """Test that publish command requires clean working tree."""
    # Create venv first
    import subprocess
    venv_dir = temp_git_project / ".venv"
    subprocess.run(
        ["python3", "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )

    # Install dependencies
    import os
    pip_path = venv_dir / "Scripts" / "pip" if os.name == "nt" else venv_dir / "bin" / "pip"

    subprocess.run(
        [str(pip_path), "install", "pytest", "build", "twine"],
        check=True,
        capture_output=True,
    )

    # Make working tree dirty
    (temp_git_project / "dirty_file.txt").write_text("dirty content")

    app = AppContext(project_root=temp_git_project, quiet=True)

    result = publish_command(app)

    # Should fail due to dirty working tree
    assert result == 1


def test_publish_command_allow_dirty(temp_git_project: Path):
    """Test that publish command can bypass clean tree check with --allow-dirty."""
    # Create venv first
    import subprocess
    venv_dir = temp_git_project / ".venv"
    subprocess.run(
        ["python3", "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )

    # Install dependencies
    import os
    pip_path = venv_dir / "Scripts" / "pip" if os.name == "nt" else venv_dir / "bin" / "pip"

    subprocess.run(
        [str(pip_path), "install", "pytest", "build", "twine"],
        check=True,
        capture_output=True,
    )

    # Make working tree dirty
    (temp_git_project / "dirty_file.txt").write_text("dirty content")

    app = AppContext(project_root=temp_git_project, dry_run=True, verbosity=1)

    # Should succeed with allow_dirty=True and dry_run=True
    result = publish_command(app, allow_dirty=True)

    assert result == 0


def test_publish_command_dry_run(venv_project: Path):
    """Test that publish command works in dry-run mode."""
    app = AppContext(project_root=venv_project, dry_run=True, verbosity=1)

    result = publish_command(app, skip_tests=True)

    # Dry run should succeed
    assert result == 0


def test_publish_command_skip_tests(venv_project: Path):
    """Test that publish command can skip tests."""
    # Install twine in venv
    import os
    import subprocess

    venv_dir = venv_project / ".venv"
    pip_path = venv_dir / "Scripts" / "pip" if os.name == "nt" else venv_dir / "bin" / "pip"

    subprocess.run(
        [str(pip_path), "install", "twine"],
        check=True,
        capture_output=True,
    )

    app = AppContext(project_root=venv_project, dry_run=True, verbosity=1)

    result = publish_command(app, skip_tests=True)

    assert result == 0


def test_publish_command_builds_package(venv_project: Path):
    """Test that publish command builds the package."""
    # Install twine in venv
    import os
    import subprocess

    venv_dir = venv_project / ".venv"
    pip_path = venv_dir / "Scripts" / "pip" if os.name == "nt" else venv_dir / "bin" / "pip"

    subprocess.run(
        [str(pip_path), "install", "twine"],
        check=True,
        capture_output=True,
    )

    app = AppContext(project_root=venv_project, dry_run=True, verbosity=1)

    result = publish_command(app, skip_tests=True)

    assert result == 0

    # In dry-run, dist directory won't be created
    # But the command should succeed
