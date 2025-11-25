"""Virtual environment management commands for devflow.

This module is owned by Workstream C (Venv & Dependency Management).
It implements the `devflow venv init` command and related functionality.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import venv
from pathlib import Path
from typing import TYPE_CHECKING

from devflow.core.paths import (
    get_venv_dir,
    get_venv_python,
    venv_exists,
)

if TYPE_CHECKING:
    from typing import Optional


class VenvManager:
    """Manages virtual environment creation and configuration.

    This class provides the core venv functionality. Other workstreams
    should use the path helpers in core/paths.py for venv-aware operations.

    Attributes:
        project_root: Path to the project root directory.
        venv_dir_name: Name of the venv directory (e.g., ".venv").
        default_python: Default Python interpreter to use.
        verbose: Whether to enable verbose output.
        dry_run: Whether to perform a dry run (no actual changes).
        quiet: Whether to suppress output.
    """

    def __init__(
        self,
        project_root: Path,
        venv_dir_name: str = ".venv",
        default_python: Optional[str] = None,
        verbose: bool = False,
        dry_run: bool = False,
        quiet: bool = False,
    ):
        """Initialize the VenvManager.

        Args:
            project_root: Path to the project root directory.
            venv_dir_name: Name of the venv directory. Defaults to ".venv".
            default_python: Default Python interpreter. Defaults to sys.executable.
            verbose: Enable verbose output.
            dry_run: Perform dry run without making changes.
            quiet: Suppress non-error output.
        """
        self.project_root = Path(project_root).resolve()
        self.venv_dir_name = venv_dir_name
        self.default_python = default_python or sys.executable
        self.verbose = verbose
        self.dry_run = dry_run
        self.quiet = quiet

    @property
    def venv_dir(self) -> Path:
        """Get the full path to the venv directory."""
        return get_venv_dir(self.project_root, self.venv_dir_name)

    def _log(self, message: str, level: str = "info") -> None:
        """Log a message with the appropriate prefix.

        Args:
            message: The message to log.
            level: Log level ("info", "debug", "error").
        """
        if self.quiet and level != "error":
            return

        if level == "debug" and not self.verbose:
            return

        prefix = "[venv]"
        if level == "error":
            prefix = "[venv] ERROR:"
        elif level == "debug":
            prefix = "[venv] DEBUG:"

        print(f"{prefix} {message}")

    def _resolve_python(self, python: Optional[str] = None) -> str:
        """Resolve the Python interpreter to use.

        Args:
            python: Explicit Python path or version string.

        Returns:
            Path to the Python executable.

        Raises:
            FileNotFoundError: If the Python interpreter is not found.
        """
        if python:
            # If it's a path, use it directly
            python_path = Path(python)
            if python_path.exists():
                return str(python_path.resolve())

            # Try to find it in PATH
            resolved = shutil.which(python)
            if resolved:
                return resolved

            # Try common version patterns (e.g., python3.11)
            if python.startswith("python") or python.startswith("3."):
                version_str = python.replace("python", "")
                for name in [f"python{version_str}", f"python{version_str.split('.')[0]}"]:
                    resolved = shutil.which(name)
                    if resolved:
                        return resolved

            raise FileNotFoundError(f"Python interpreter not found: {python}")

        # Use default Python
        default = self.default_python
        if Path(default).exists():
            return str(Path(default).resolve())

        resolved = shutil.which(default)
        if resolved:
            return resolved

        # Fall back to sys.executable
        return sys.executable

    def init(
        self,
        python: Optional[str] = None,
        recreate: bool = False,
        with_pip: bool = True,
        system_site_packages: bool = False,
    ) -> int:
        """Create a virtual environment.

        Implements `devflow venv init` honoring default_python, venv_dir,
        --python, and --recreate. Ensures idempotent creation with clear logs.

        Args:
            python: Python interpreter to use (overrides default_python).
            recreate: If True, delete and recreate existing venv.
            with_pip: Whether to install pip in the venv.
            system_site_packages: Whether to give access to system site-packages.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        venv_path = self.venv_dir

        # Resolve the Python interpreter
        try:
            python_path = self._resolve_python(python)
        except FileNotFoundError as e:
            self._log(str(e), level="error")
            return 1

        self._log(f"Using Python: {python_path}", level="debug")

        # Check if venv already exists
        if venv_exists(venv_path):
            if recreate:
                self._log(f"Recreating venv at {venv_path}")
                if not self.dry_run:
                    try:
                        shutil.rmtree(venv_path)
                    except Exception as e:
                        self._log(f"Failed to remove existing venv: {e}", level="error")
                        return 1
            else:
                self._log(f"Virtual environment already exists at {venv_path}")
                # Verify Python version matches
                existing_python = get_venv_python(venv_path)
                if existing_python.exists():
                    self._log(f"Existing venv Python: {existing_python}", level="debug")
                self._log("Use --recreate to rebuild the venv")
                return 0

        # Create the venv
        self._log(f"Creating virtual environment at {venv_path}")

        if self.dry_run:
            self._log("DRY RUN: Would create venv with the following settings:")
            self._log(f"  Python: {python_path}", level="debug")
            self._log(f"  with_pip: {with_pip}", level="debug")
            self._log(f"  system_site_packages: {system_site_packages}", level="debug")
            return 0

        try:
            # Use subprocess to call the resolved Python with venv module
            # This ensures we use the correct Python version
            cmd = [
                python_path,
                "-m",
                "venv",
                str(venv_path),
            ]

            if system_site_packages:
                cmd.append("--system-site-packages")

            if not with_pip:
                cmd.append("--without-pip")

            self._log(f"Running: {' '.join(cmd)}", level="debug")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                self._log(f"Failed to create venv: {result.stderr}", level="error")
                return result.returncode

            # Verify the venv was created
            if not venv_exists(venv_path):
                self._log("Venv creation reported success but venv not found", level="error")
                return 1

            self._log(f"Virtual environment created successfully at {venv_path}")

            # Log the venv Python version
            venv_python = get_venv_python(venv_path)
            if venv_python.exists():
                version_result = subprocess.run(
                    [str(venv_python), "--version"],
                    capture_output=True,
                    text=True,
                )
                if version_result.returncode == 0:
                    self._log(f"Venv Python version: {version_result.stdout.strip()}", level="debug")

            return 0

        except Exception as e:
            self._log(f"Error creating virtual environment: {e}", level="error")
            return 1

    def delete(self) -> int:
        """Delete the virtual environment.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        venv_path = self.venv_dir

        if not venv_path.exists():
            self._log(f"Virtual environment does not exist at {venv_path}")
            return 0

        self._log(f"Deleting virtual environment at {venv_path}")

        if self.dry_run:
            self._log("DRY RUN: Would delete venv")
            return 0

        try:
            shutil.rmtree(venv_path)
            self._log("Virtual environment deleted successfully")
            return 0
        except Exception as e:
            self._log(f"Failed to delete venv: {e}", level="error")
            return 1

    def info(self) -> int:
        """Display information about the virtual environment.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        venv_path = self.venv_dir

        if not venv_exists(venv_path):
            self._log(f"Virtual environment does not exist at {venv_path}")
            return 1

        venv_python = get_venv_python(venv_path)

        print(f"Venv Path: {venv_path}")
        print(f"Venv Python: {venv_python}")

        # Get Python version
        if venv_python.exists():
            result = subprocess.run(
                [str(venv_python), "--version"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"Python Version: {result.stdout.strip()}")

            # Get pip version
            pip_result = subprocess.run(
                [str(venv_python), "-m", "pip", "--version"],
                capture_output=True,
                text=True,
            )
            if pip_result.returncode == 0:
                print(f"Pip Version: {pip_result.stdout.strip()}")

        return 0


def create_venv_manager(
    project_root: Optional[Path] = None,
    venv_dir: str = ".venv",
    default_python: Optional[str] = None,
    verbose: bool = False,
    dry_run: bool = False,
    quiet: bool = False,
) -> VenvManager:
    """Factory function to create a VenvManager.

    This is the recommended way for other workstreams to get a VenvManager
    instance. It handles project root detection if not provided.

    Args:
        project_root: Project root path. If None, will attempt to find it.
        venv_dir: Name of the venv directory.
        default_python: Default Python interpreter.
        verbose: Enable verbose output.
        dry_run: Perform dry run.
        quiet: Suppress output.

    Returns:
        Configured VenvManager instance.

    Raises:
        RuntimeError: If project_root is None and cannot be determined.
    """
    from devflow.core.paths import find_project_root

    if project_root is None:
        project_root = find_project_root()

    return VenvManager(
        project_root=project_root,
        venv_dir_name=venv_dir,
        default_python=default_python,
        verbose=verbose,
        dry_run=dry_run,
        quiet=quiet,
    )
