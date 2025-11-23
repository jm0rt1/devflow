"""Path utilities and project root detection."""

from pathlib import Path


def find_project_root(start: Path | None = None) -> Path:
    """
    Find the project root by walking up from the start path.

    Looks for pyproject.toml or devflow.toml.

    Args:
        start: Starting path. If None, uses current working directory.

    Returns:
        Path to the project root.

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
        "Project root not found. Looking for pyproject.toml or devflow.toml. "
        "Use --project-root to specify explicitly."
    )
