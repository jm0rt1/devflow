"""Dependency management commands."""

import subprocess
from pathlib import Path
from typing import List

from devflow.commands.base import Command
from devflow.core.paths import get_venv_pip


class DepsSyncCommand(Command):
    """Sync dependencies from requirements files."""

    name = "deps-sync"
    help = "Install dependencies from requirements files"

    def run(self) -> int:
        """
        Sync dependencies.

        Returns:
            Exit code (0 for success)
        """
        venv_dir = self.app.get_venv_dir()

        # Check if venv exists
        if not venv_dir.exists():
            self.app.logger.error(
                f"Venv not found at {venv_dir}. Run 'devflow venv init' first.",
                prefix="deps",
            )
            return 1

        # Get requirements files
        requirements_files = self._get_requirements_files()

        if not requirements_files:
            self.app.logger.warning(
                "No requirements files found to sync",
                prefix="deps",
            )
            return 0

        self.app.logger.info(
            f"Syncing dependencies from {len(requirements_files)} file(s)",
            prefix="deps",
        )

        # Get pip path
        try:
            pip_path = get_venv_pip(venv_dir)
        except RuntimeError as e:
            self.app.logger.error(str(e), prefix="deps")
            return 1

        # Install from each requirements file
        for req_file in requirements_files:
            self.app.logger.info(f"Installing from {req_file}", prefix="deps")

            if self.app.dry_run:
                self.app.logger.info(
                    f"(dry-run) Would run: {pip_path} install -r {req_file}",
                    prefix="deps",
                )
                continue

            result = subprocess.run(
                [str(pip_path), "install", "-r", str(req_file)],
                capture_output=self.app.verbosity < 2,
                text=True,
                cwd=self.app.project_root,
                shell=False,
            )

            if result.returncode != 0:
                self.app.logger.error(
                    f"Failed to install from {req_file}",
                    prefix="deps",
                )
                if result.stderr and self.app.verbosity < 2:
                    self.app.logger.error(result.stderr, prefix="deps")
                return result.returncode

        self.app.logger.info("Dependencies synced successfully", prefix="deps")
        return 0

    def _get_requirements_files(self) -> List[Path]:
        """Get list of requirements files to install from."""
        files = []

        # Main requirements file
        main_req = self.app.project_root / self.app.config.deps.requirements
        if main_req.exists():
            files.append(main_req)

        # Dev requirements file
        if self.app.config.deps.dev_requirements:
            dev_req = self.app.project_root / self.app.config.deps.dev_requirements
            if dev_req.exists():
                files.append(dev_req)

        return files


class DepsFreezeCommand(Command):
    """Freeze installed dependencies to a file."""

    name = "deps-freeze"
    help = "Freeze installed dependencies to a file"

    def run(self) -> int:
        """
        Freeze dependencies.

        Returns:
            Exit code (0 for success)
        """
        venv_dir = self.app.get_venv_dir()

        # Check if venv exists
        if not venv_dir.exists():
            self.app.logger.error(
                f"Venv not found at {venv_dir}. Run 'devflow venv init' first.",
                prefix="deps",
            )
            return 1

        # Get output file path
        freeze_output = self.app.project_root / self.app.config.deps.freeze_output

        self.app.logger.info(
            f"Freezing dependencies to {freeze_output}",
            prefix="deps",
        )

        # Get pip path
        try:
            pip_path = get_venv_pip(venv_dir)
        except RuntimeError as e:
            self.app.logger.error(str(e), prefix="deps")
            return 1

        if self.app.dry_run:
            self.app.logger.info(
                f"(dry-run) Would run: {pip_path} freeze > {freeze_output}",
                prefix="deps",
            )
            return 0

        # Run pip freeze
        result = subprocess.run(
            [str(pip_path), "freeze"],
            capture_output=True,
            text=True,
            cwd=self.app.project_root,
            shell=False,
        )

        if result.returncode != 0:
            self.app.logger.error(
                f"Failed to freeze dependencies: {result.stderr}",
                prefix="deps",
            )
            return result.returncode

        # Sort output for deterministic results
        lines = result.stdout.strip().split("\n")
        lines = [line for line in lines if line.strip()]  # Remove empty lines
        lines.sort()  # Sort alphabetically

        # Write to file
        try:
            with open(freeze_output, "w") as f:
                f.write("\n".join(lines))
                f.write("\n")  # Add trailing newline

            self.app.logger.info(
                f"Successfully froze {len(lines)} packages to {freeze_output}",
                prefix="deps",
            )
            return 0

        except Exception as e:
            self.app.logger.error(
                f"Failed to write freeze output: {e}",
                prefix="deps",
            )
            return 1
