"""Pytest configuration and fixtures."""

import subprocess
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary git repository for testing.

    Yields:
        Path to the temporary git repository
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Configure git user for commits
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    readme = repo_path / "README.md"
    readme.write_text("# Test Repository\n")
    subprocess.run(
        ["git", "add", "README.md"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=repo_path,
        check=True,
        capture_output=True,
    )

    yield repo_path


@pytest.fixture
def dirty_git_repo(temp_git_repo: Path) -> Path:
    """
    Create a git repository with uncommitted changes.

    Args:
        temp_git_repo: Base temporary git repository

    Returns:
        Path to the dirty git repository
    """
    # Create a new file without committing
    new_file = temp_git_repo / "uncommitted.txt"
    new_file.write_text("Uncommitted changes\n")

    return temp_git_repo


@pytest.fixture
def git_repo_with_tags(temp_git_repo: Path) -> Path:
    """
    Create a git repository with version tags.

    Args:
        temp_git_repo: Base temporary git repository

    Returns:
        Path to the git repository with tags
    """
    # Create a few tags
    subprocess.run(
        ["git", "tag", "v0.1.0"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    # Make another commit
    file2 = temp_git_repo / "file2.txt"
    file2.write_text("Second file\n")
    subprocess.run(
        ["git", "add", "file2.txt"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Add file2"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    # Create another tag
    subprocess.run(
        ["git", "tag", "v1.0.0"],
        cwd=temp_git_repo,
        check=True,
        capture_output=True,
    )

    return temp_git_repo
