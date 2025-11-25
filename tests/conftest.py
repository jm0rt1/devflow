"""
Pytest configuration for devflow tests.

This module provides common fixtures and configuration for all tests.
"""

import subprocess
import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest


@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """
    Create a temporary directory for test projects.

    Yields:
        Path: Path to the temporary directory.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def temp_git_repo(temp_project_dir: Path) -> Generator[Path, None, None]:
    """
    Create a temporary git repository for testing git-related functionality.

    Yields:
        Path: Path to the temporary git repository.
    """
    # Initialize git repo
    subprocess.run(
        ["git", "init"],
        cwd=temp_project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_project_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project_dir,
        check=True,
        capture_output=True,
    )

    yield temp_project_dir


@pytest.fixture
def sample_pyproject_toml() -> str:
    """
    Return a sample pyproject.toml content with devflow configuration.

    Returns:
        str: Sample pyproject.toml content.
    """
    return """
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"

[tool.devflow]
venv_dir = ".venv"
default_python = "python3"
test_runner = "pytest"

[tool.devflow.tasks.test]
command = "pytest"
args = ["-q"]
use_venv = true

[tool.devflow.tasks.build]
command = "python"
args = ["-m", "build"]
use_venv = true

[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test"]

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]
"""
