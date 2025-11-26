"""Project root detection and path helpers for devflow.

Provides utilities for detecting the project root by walking upward
from the current directory until a marker file (pyproject.toml or
devflow.toml) is found.
"""

from __future__ import annotations

from pathlib import Path


class ProjectRootNotFoundError(Exception):
    """Raised when project root cannot be detected."""

def find_project_root(start: Path | None = None) -> Path:
    """Find the project root by walking upward from start directory.

    The project root is identified by the presence of either:
    - pyproject.toml
    - devflow.toml

    Args:
        start: Starting directory for the search. Defaults to current directory.

    Returns:
        Path to the project root directory.

    Raises:
        ProjectRootNotFoundError: If no project root markers are found.
    """
    if start is None:
        start = Path.cwd()

    # Ensure we have an absolute path
    current = start.resolve()

    while True:
        # Check for project root markers
        if (current / "pyproject.toml").exists():
            return current
        if (current / "devflow.toml").exists():
            return current

        # Move up to parent
        parent = current.parent

        # Check if we've reached the filesystem root
        if parent == current:
            raise ProjectRootNotFoundError(
                f"Project root not found. Searched from '{start}' to filesystem root. "
                "Ensure your project has a pyproject.toml or devflow.toml file."
            )

        current = parent


def resolve_path(base: Path, relative: str) -> Path:
    """Resolve a relative path against a base directory.

    Args:
        base: Base directory (typically project root).
        relative: Relative path string.

    Returns:
        Resolved absolute path.
    """
    return (base / relative).resolve()
