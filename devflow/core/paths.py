"""Path utilities for project root detection."""

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """
    Find the project root by walking upward until finding pyproject.toml or devflow.toml.

    Args:
        start: Starting directory. If None, uses current working directory.

    Returns:
        Path to project root.

    Raises:
        RuntimeError: If no project root is found.
    """
    if start is None:
        start = Path.cwd()

    current = start.resolve()

    # Walk up the directory tree
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "devflow.toml").exists():
            return current
        current = current.parent

    raise RuntimeError(
        f"Project root not found. No pyproject.toml or devflow.toml found "
        f"in {start} or any parent directory."
    )
