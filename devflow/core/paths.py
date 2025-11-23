"""Path utilities for devflow."""

import os
from pathlib import Path
from typing import Optional


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Find the project root by walking up until we find pyproject.toml or devflow.toml.

    Args:
        start: Starting directory (defaults to current working directory)

    Returns:
        Path to project root

    Raises:
        RuntimeError: If project root cannot be found
    """
    current = start or Path.cwd()

    # Ensure we start with an absolute path
    current = current.resolve()

    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "devflow.toml").exists():
            return current
        current = current.parent

    raise RuntimeError(
        "Project root not found. Looking for pyproject.toml or devflow.toml. "
        f"Started search from: {start or Path.cwd()}"
    )


def get_venv_python(venv_dir: Path) -> Path:
    """
    Get the path to the Python executable in a virtual environment.

    Args:
        venv_dir: Path to the virtual environment

    Returns:
        Path to the Python executable
    """
    if os.name == "nt":  # Windows
        return venv_dir / "Scripts" / "python.exe"
    else:  # Unix-like
        return venv_dir / "bin" / "python"


def get_venv_executable(venv_dir: Path, executable: str) -> Path:
    """
    Get the path to an executable in a virtual environment.

    Args:
        venv_dir: Path to the virtual environment
        executable: Name of the executable

    Returns:
        Path to the executable
    """
    if os.name == "nt":  # Windows
        # Try with .exe extension first
        exe_path = venv_dir / "Scripts" / f"{executable}.exe"
        if exe_path.exists():
            return exe_path
        # Try without extension
        return venv_dir / "Scripts" / executable
    else:  # Unix-like
        return venv_dir / "bin" / executable
