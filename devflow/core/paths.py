"""Path utilities for project root detection and path resolution."""

from pathlib import Path
from typing import Optional


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Find the project root by walking up from the start directory.

    Looks for pyproject.toml or devflow.toml to identify the project root.

    Args:
        start: Starting directory for the search. Defaults to current directory.

    Returns:
        Path to the project root directory.

    Raises:
        RuntimeError: If no project root is found.
    """
    current = start or Path.cwd()
    current = current.resolve()

    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "devflow.toml").exists():
            return current
        current = current.parent

    raise RuntimeError(
        "Project root not found. No pyproject.toml or devflow.toml found in current "
        "directory or any parent directory."
    )


def get_venv_python(venv_dir: Path) -> Path:
    """
    Get the path to the Python executable inside a venv.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        Path to the Python executable.
    """
    if (venv_dir / "bin" / "python").exists():
        # Unix-like systems
        return venv_dir / "bin" / "python"
    elif (venv_dir / "Scripts" / "python.exe").exists():
        # Windows
        return venv_dir / "Scripts" / "python.exe"
    else:
        raise RuntimeError(f"Python executable not found in venv: {venv_dir}")


def get_venv_pip(venv_dir: Path) -> Path:
    """
    Get the path to the pip executable inside a venv.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        Path to the pip executable.
    """
    if (venv_dir / "bin" / "pip").exists():
        # Unix-like systems
        return venv_dir / "bin" / "pip"
    elif (venv_dir / "Scripts" / "pip.exe").exists():
        # Windows
        return venv_dir / "Scripts" / "pip.exe"
    else:
        raise RuntimeError(f"pip executable not found in venv: {venv_dir}")
