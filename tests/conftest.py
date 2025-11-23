"""Pytest configuration and fixtures."""

import os
import shutil
import subprocess
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_project(tmp_path: Path) -> Generator[Path, None, None]:
    """
    Create a temporary project with a basic structure.

    Yields:
        Path to temporary project directory
    """
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create pyproject.toml
    pyproject_content = """[build-system]
requires = ["setuptools>=68.0.0"]
build-backend = "setuptools.build_meta"

[project]
name = "test-project"
version = "0.1.0"
description = "Test project"
requires-python = ">=3.8"

[tool.devflow]
venv_dir = ".venv"
test_runner = "pytest"
build_backend = "build"

[tool.devflow.publish]
repository = "testpypi"
tag_on_publish = true
tag_format = "v{version}"
require_clean_working_tree = true
run_tests_before_publish = false
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content)

    # Create a simple package structure
    src_dir = project_dir / "src" / "test_project"
    src_dir.mkdir(parents=True)
    (src_dir / "__init__.py").write_text('__version__ = "0.1.0"\n')

    # Create a simple test
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_basic.py").write_text("""
def test_passing():
    assert True

def test_example():
    assert 1 + 1 == 2
""")

    yield project_dir

    # Cleanup
    if project_dir.exists():
        shutil.rmtree(project_dir)


@pytest.fixture
def temp_git_project(temp_project: Path) -> Path:
    """
    Create a temporary project with git initialized.

    Args:
        temp_project: Temporary project fixture

    Returns:
        Path to temporary project directory with git
    """
    # Initialize git
    subprocess.run(
        ["git", "init"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )

    # Configure git
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )

    # Add and commit files
    subprocess.run(
        ["git", "add", "."],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=temp_project,
        check=True,
        capture_output=True,
    )

    return temp_project


@pytest.fixture
def venv_project(temp_project: Path) -> Path:
    """
    Create a temporary project with a virtual environment.

    Args:
        temp_project: Temporary project fixture

    Returns:
        Path to temporary project directory with venv
    """
    venv_dir = temp_project / ".venv"

    # Create virtual environment
    subprocess.run(
        ["python3", "-m", "venv", str(venv_dir)],
        check=True,
        capture_output=True,
    )

    # Get pip path
    pip_path = venv_dir / "Scripts" / "pip" if os.name == "nt" else venv_dir / "bin" / "pip"

    # Install pytest and build in venv
    subprocess.run(
        [str(pip_path), "install", "pytest", "build"],
        check=True,
        capture_output=True,
    )

    return temp_project
