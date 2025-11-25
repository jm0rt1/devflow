"""Path utilities and venv-aware helpers for devflow.

This module is owned by Workstream C (Venv & Dependency Management).
Other workstreams should import these helpers rather than implementing
their own environment handling logic.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Optional


def find_project_root(start: Optional[Path] = None) -> Path:
    """Walk upward from start until finding pyproject.toml or devflow.toml.

    Args:
        start: Starting directory. Defaults to current working directory.

    Returns:
        Path to the project root directory.

    Raises:
        RuntimeError: If no project root marker is found.
    """
    if start is None:
        start = Path.cwd()
    else:
        start = Path(start).resolve()

    current = start
    while current != current.parent:
        if (current / "pyproject.toml").exists() or (current / "devflow.toml").exists():
            return current
        current = current.parent

    # Check the root itself (e.g., for '/')
    if (current / "pyproject.toml").exists() or (current / "devflow.toml").exists():
        return current

    raise RuntimeError(
        f"Project root not found. No pyproject.toml or devflow.toml found "
        f"in {start} or any parent directory."
    )


def get_venv_dir(project_root: Path, venv_dir: str = ".venv") -> Path:
    """Get the virtual environment directory path.

    Args:
        project_root: The project root directory.
        venv_dir: Name of the venv directory (from config). Defaults to ".venv".

    Returns:
        Absolute path to the venv directory.
    """
    venv_path = project_root / venv_dir
    return venv_path.resolve()


def get_venv_python(venv_dir: Path) -> Path:
    """Get the Python executable path inside a virtual environment.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        Path to the Python executable.

    Raises:
        FileNotFoundError: If the venv Python executable is not found.
    """
    if sys.platform == "win32":
        python_path = venv_dir / "Scripts" / "python.exe"
    else:
        python_path = venv_dir / "bin" / "python"

    return python_path


def get_venv_pip(venv_dir: Path) -> Path:
    """Get the pip executable path inside a virtual environment.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        Path to the pip executable.
    """
    if sys.platform == "win32":
        pip_path = venv_dir / "Scripts" / "pip.exe"
    else:
        pip_path = venv_dir / "bin" / "pip"

    return pip_path


def get_venv_bin_dir(venv_dir: Path) -> Path:
    """Get the bin/Scripts directory inside a virtual environment.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        Path to the bin (Unix) or Scripts (Windows) directory.
    """
    if sys.platform == "win32":
        return venv_dir / "Scripts"
    else:
        return venv_dir / "bin"


def is_venv_active(venv_dir: Path) -> bool:
    """Check if the specified virtual environment is currently active.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        True if the venv is active, False otherwise.
    """
    virtual_env = os.environ.get("VIRTUAL_ENV")
    if virtual_env is None:
        return False
    return Path(virtual_env).resolve() == venv_dir.resolve()


def venv_exists(venv_dir: Path) -> bool:
    """Check if a virtual environment exists at the given path.

    Args:
        venv_dir: Path to the virtual environment directory.

    Returns:
        True if the venv exists and appears valid, False otherwise.
    """
    python_path = get_venv_python(venv_dir)
    return venv_dir.is_dir() and python_path.exists()


def get_venv_env(venv_dir: Path, extra_env: Optional[dict[str, str]] = None) -> dict[str, str]:
    """Get environment variables for running commands inside a venv.

    This helper creates the environment dict needed to run subprocess
    commands inside the virtual environment. Other workstreams should
    use this instead of manually constructing venv environments.

    Args:
        venv_dir: Path to the virtual environment directory.
        extra_env: Additional environment variables to include.

    Returns:
        Dictionary of environment variables for subprocess calls.
    """
    env = os.environ.copy()
    bin_dir = get_venv_bin_dir(venv_dir)

    # Set VIRTUAL_ENV
    env["VIRTUAL_ENV"] = str(venv_dir.resolve())

    # Prepend the venv bin directory to PATH
    current_path = env.get("PATH", "")
    env["PATH"] = f"{bin_dir}{os.pathsep}{current_path}"

    # Remove PYTHONHOME if set (can interfere with venv)
    env.pop("PYTHONHOME", None)

    # Apply extra environment variables
    if extra_env:
        env.update(extra_env)

    return env


def build_venv_command(
    venv_dir: Path,
    command: list[str],
    use_venv: bool = True,
) -> tuple[list[str], dict[str, str]]:
    """Build a command and environment for execution, optionally using venv.

    This is the primary helper for other workstreams to use when executing
    commands that should run inside the project's virtual environment.

    Args:
        venv_dir: Path to the virtual environment directory.
        command: Command and arguments to run (e.g., ["pytest", "-q"]).
        use_venv: Whether to execute inside the venv. Defaults to True.

    Returns:
        Tuple of (modified command, environment dict).

    Raises:
        FileNotFoundError: If use_venv is True and the venv doesn't exist.

    Example:
        >>> venv_dir = Path(".venv")
        >>> cmd, env = build_venv_command(venv_dir, ["pytest", "-v"])
        >>> subprocess.run(cmd, env=env)  # Runs pytest from venv
    """
    if not use_venv:
        # Return original command with current environment
        return command, os.environ.copy()

    if not venv_exists(venv_dir):
        raise FileNotFoundError(
            f"Virtual environment not found at {venv_dir}. "
            f"Run 'devflow venv init' first."
        )

    # Get venv environment
    env = get_venv_env(venv_dir)

    # For executable commands (like pytest, pip, python), resolve to venv path
    # if the command is a known executable in the venv
    if command:
        executable = command[0]
        bin_dir = get_venv_bin_dir(venv_dir)

        # Check if it's a Python module invocation
        if executable == "python" or executable == "python3":
            venv_python = get_venv_python(venv_dir)
            command = [str(venv_python)] + command[1:]
        else:
            # Try to find the executable in the venv bin directory
            if sys.platform == "win32":
                possible_paths = [
                    bin_dir / f"{executable}.exe",
                    bin_dir / f"{executable}.cmd",
                    bin_dir / executable,
                ]
            else:
                possible_paths = [bin_dir / executable]

            for possible_path in possible_paths:
                if possible_path.exists():
                    command = [str(possible_path)] + command[1:]
                    break

    return command, env


def resolve_requirements_files(
    project_root: Path,
    requirements: Optional[str] = None,
    dev_requirements: Optional[str] = None,
    include_dev: bool = True,
) -> list[Path]:
    """Resolve requirements file paths based on config and existence.

    Args:
        project_root: The project root directory.
        requirements: Main requirements file name from config.
        dev_requirements: Dev requirements file name from config.
        include_dev: Whether to include dev requirements.

    Returns:
        List of existing requirements file paths.
    """
    files = []

    # Default requirements file
    default_req = project_root / "requirements.txt"
    if requirements:
        req_path = project_root / requirements
        if req_path.exists():
            files.append(req_path)
    elif default_req.exists():
        files.append(default_req)

    # Dev requirements
    if include_dev:
        default_dev_req = project_root / "requirements-dev.txt"
        if dev_requirements:
            dev_path = project_root / dev_requirements
            if dev_path.exists():
                files.append(dev_path)
        elif default_dev_req.exists():
            files.append(default_dev_req)

    return files


def has_pyproject_dependencies(project_root: Path) -> bool:
    """Check if pyproject.toml has dependency specifications.

    Args:
        project_root: The project root directory.

    Returns:
        True if pyproject.toml exists and has dependencies defined.
    """
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.exists():
        return False

    try:
        # Use tomllib (Python 3.11+) or tomli as fallback
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore

        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Check for PEP 621 dependencies
        if "project" in data and "dependencies" in data["project"]:
            return True

        # Check for build-system requirements
        if "build-system" in data and "requires" in data["build-system"]:
            return True

        return False

    except Exception:
        return False
