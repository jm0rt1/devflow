"""Dependency management commands for devflow.

This module is owned by Workstream C (Venv & Dependency Management).
It implements `devflow deps sync` and `devflow deps freeze` commands.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from devflow.core.paths import (
    build_venv_command,
    get_venv_dir,
    get_venv_pip,
    get_venv_python,
    has_pyproject_dependencies,
    resolve_requirements_files,
    venv_exists,
)

if TYPE_CHECKING:
    from typing import Optional


class DepsManager:
    """Manages dependency installation and freezing.

    This class provides dependency management functionality.
    Other workstreams should use this class for dependency operations.

    Attributes:
        project_root: Path to the project root directory.
        venv_dir_name: Name of the venv directory.
        requirements: Main requirements file name.
        dev_requirements: Dev requirements file name.
        freeze_output: Path for freeze output file.
        verbose: Whether to enable verbose output.
        dry_run: Whether to perform a dry run.
        quiet: Whether to suppress output.
    """

    def __init__(
        self,
        project_root: Path,
        venv_dir_name: str = ".venv",
        requirements: Optional[str] = None,
        dev_requirements: Optional[str] = None,
        freeze_output: str = "requirements-freeze.txt",
        verbose: bool = False,
        dry_run: bool = False,
        quiet: bool = False,
    ):
        """Initialize the DepsManager.

        Args:
            project_root: Path to the project root directory.
            venv_dir_name: Name of the venv directory.
            requirements: Main requirements file name.
            dev_requirements: Dev requirements file name.
            freeze_output: Path for freeze output file.
            verbose: Enable verbose output.
            dry_run: Perform dry run without making changes.
            quiet: Suppress non-error output.
        """
        self.project_root = Path(project_root).resolve()
        self.venv_dir_name = venv_dir_name
        self.requirements = requirements
        self.dev_requirements = dev_requirements
        self.freeze_output = freeze_output
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

        prefix = "[deps]"
        if level == "error":
            prefix = "[deps] ERROR:"
        elif level == "debug":
            prefix = "[deps] DEBUG:"

        print(f"{prefix} {message}")

    def _ensure_venv(self) -> bool:
        """Ensure the virtual environment exists.

        Returns:
            True if venv exists, False otherwise.
        """
        if not venv_exists(self.venv_dir):
            self._log(
                f"Virtual environment not found at {self.venv_dir}. "
                f"Run 'devflow venv init' first.",
                level="error",
            )
            return False
        return True

    def _run_pip(
        self,
        args: list[str],
        check: bool = True,
    ) -> subprocess.CompletedProcess:
        """Run pip command in the venv.

        Args:
            args: Arguments to pass to pip.
            check: Whether to check for non-zero exit code.

        Returns:
            CompletedProcess instance.
        """
        venv_python = get_venv_python(self.venv_dir)
        cmd = [str(venv_python), "-m", "pip"] + args

        self._log(f"Running: {' '.join(cmd)}", level="debug")

        if self.dry_run:
            self._log(f"DRY RUN: Would run: {' '.join(cmd)}")
            # Return a mock result for dry run
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=0,
                stdout="",
                stderr="",
            )

        result = subprocess.run(
            cmd,
            capture_output=not self.verbose,
            text=True,
        )

        return result

    def sync(
        self,
        include_dev: bool = True,
        extras: Optional[list[str]] = None,
        upgrade: bool = False,
    ) -> int:
        """Sync dependencies from requirements files or pyproject.toml.

        Implements `devflow deps sync` to install from requirements.txt,
        pyproject.toml, or requirements-*.txt according to config.

        Args:
            include_dev: Whether to include dev dependencies.
            extras: Optional list of extras to install (stub for future).
            upgrade: Whether to upgrade packages to latest versions.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        if not self._ensure_venv():
            return 1

        self._log("Syncing dependencies")

        # Collect all requirements files
        req_files = resolve_requirements_files(
            self.project_root,
            self.requirements,
            self.dev_requirements,
            include_dev=include_dev,
        )

        # Check for pyproject.toml dependencies
        has_pyproject_deps = has_pyproject_dependencies(self.project_root)

        if not req_files and not has_pyproject_deps:
            self._log("No requirements files or pyproject.toml dependencies found")
            return 0

        exit_code = 0

        # Install from pyproject.toml if it has dependencies
        if has_pyproject_deps:
            self._log(f"Installing from pyproject.toml")

            install_args = ["install", "-e", str(self.project_root)]

            if upgrade:
                install_args.append("--upgrade")

            # Handle extras (stub - can be extended later)
            if extras:
                extras_str = ",".join(extras)
                install_args[-1] = f"{self.project_root}[{extras_str}]"

            result = self._run_pip(install_args)
            if result.returncode != 0:
                self._log(
                    f"Failed to install from pyproject.toml: {result.stderr}",
                    level="error",
                )
                exit_code = result.returncode

        # Install from requirements files
        for req_file in req_files:
            self._log(f"Installing from {req_file.name}")

            install_args = ["install", "-r", str(req_file)]

            if upgrade:
                install_args.append("--upgrade")

            result = self._run_pip(install_args)
            if result.returncode != 0:
                self._log(
                    f"Failed to install from {req_file.name}: {result.stderr}",
                    level="error",
                )
                exit_code = result.returncode

        if exit_code == 0:
            self._log("Dependencies synced successfully")

        return exit_code

    def freeze(
        self,
        output_path: Optional[str] = None,
        include_all: bool = False,
    ) -> int:
        """Freeze installed packages to a file.

        Implements `devflow deps freeze` writing to configured freeze_output
        path with deterministic ordering and dry-run preview support.

        Args:
            output_path: Override output path from config.
            include_all: Include all packages (including pip, setuptools, etc.).

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        if not self._ensure_venv():
            return 1

        output_file = self.project_root / (output_path or self.freeze_output)

        self._log(f"Freezing dependencies to {output_file}")

        # Get the list of installed packages
        freeze_args = ["freeze"]

        # Run pip freeze to get package list
        venv_python = get_venv_python(self.venv_dir)
        cmd = [str(venv_python), "-m", "pip"] + freeze_args

        self._log(f"Running: {' '.join(cmd)}", level="debug")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            self._log(f"Failed to freeze dependencies: {result.stderr}", level="error")
            return result.returncode

        # Parse and sort the output for deterministic ordering
        packages = result.stdout.strip().split("\n") if result.stdout.strip() else []

        # Filter out common installer packages unless include_all
        if not include_all:
            excluded_prefixes = ("pip==", "setuptools==", "wheel==")
            packages = [
                p for p in packages
                if p and not p.lower().startswith(excluded_prefixes)
            ]

        # Sort packages case-insensitively for deterministic output
        packages.sort(key=str.lower)

        # Create the output content with header
        header = [
            "# This file is auto-generated by devflow deps freeze",
            "# Do not edit manually - run 'devflow deps sync' to update dependencies",
            "#",
        ]
        content = "\n".join(header + packages) + "\n"

        if self.dry_run:
            self._log("DRY RUN: Would write the following to {output_file}:")
            print("=" * 60)
            print(content)
            print("=" * 60)
            return 0

        try:
            output_file.write_text(content)
            self._log(f"Dependencies frozen to {output_file}")
            self._log(f"Total packages: {len(packages)}", level="debug")
            return 0
        except Exception as e:
            self._log(f"Failed to write freeze file: {e}", level="error")
            return 1

    def list(self, outdated: bool = False) -> int:
        """List installed packages.

        Args:
            outdated: If True, list only outdated packages.

        Returns:
            Exit code (0 for success, non-zero for failure).
        """
        if not self._ensure_venv():
            return 1

        if outdated:
            self._log("Listing outdated packages")
            args = ["list", "--outdated", "--format=columns"]
        else:
            self._log("Listing installed packages")
            args = ["list", "--format=columns"]

        result = self._run_pip(args)

        if not self.dry_run:
            if result.stdout:
                print(result.stdout)
            if result.returncode != 0 and result.stderr:
                self._log(result.stderr, level="error")

        return result.returncode


def create_deps_manager(
    project_root: Optional[Path] = None,
    venv_dir: str = ".venv",
    requirements: Optional[str] = None,
    dev_requirements: Optional[str] = None,
    freeze_output: str = "requirements-freeze.txt",
    verbose: bool = False,
    dry_run: bool = False,
    quiet: bool = False,
) -> DepsManager:
    """Factory function to create a DepsManager.

    This is the recommended way for other workstreams to get a DepsManager
    instance. It handles project root detection if not provided.

    Args:
        project_root: Project root path. If None, will attempt to find it.
        venv_dir: Name of the venv directory.
        requirements: Main requirements file name.
        dev_requirements: Dev requirements file name.
        freeze_output: Path for freeze output file.
        verbose: Enable verbose output.
        dry_run: Perform dry run.
        quiet: Suppress output.

    Returns:
        Configured DepsManager instance.

    Raises:
        RuntimeError: If project_root is None and cannot be determined.
    """
    from devflow.core.paths import find_project_root

    if project_root is None:
        project_root = find_project_root()

    return DepsManager(
        project_root=project_root,
        venv_dir_name=venv_dir,
        requirements=requirements,
        dev_requirements=dev_requirements,
        freeze_output=freeze_output,
        verbose=verbose,
        dry_run=dry_run,
        quiet=quiet,
    )
