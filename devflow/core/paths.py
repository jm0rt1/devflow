"""Project root detection and path helpers."""

from pathlib import Path
from typing import Optional


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Find project root by walking up until pyproject.toml or devflow.toml is found.
    
    Args:
        start: Starting directory (defaults to current working directory)
        
    Returns:
        Path to project root
        
    Raises:
        RuntimeError: If no project root is found
    """
    current = start or Path.cwd()
    current = current.resolve()
    
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "devflow.toml").exists():
            return current
        current = current.parent
    
    raise RuntimeError(
        "Project root not found. Expected to find 'pyproject.toml' or 'devflow.toml' "
        "in current or parent directories."
    )


def get_venv_python(project_root: Path, venv_dir: str = ".venv") -> Path:
    """
    Get path to Python executable in the venv.
    
    Args:
        project_root: Project root directory
        venv_dir: Virtual environment directory name
        
    Returns:
        Path to Python executable
    """
    venv_path = project_root / venv_dir
    
    # Check for Windows-style venv
    win_python = venv_path / "Scripts" / "python.exe"
    if win_python.exists():
        return win_python
    
    # Unix-style venv
    unix_python = venv_path / "bin" / "python"
    if unix_python.exists():
        return unix_python
    
    raise RuntimeError(f"Virtual environment not found at {venv_path}")
