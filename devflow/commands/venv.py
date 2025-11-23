"""Virtual environment management commands."""

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional

from devflow.commands.base import Command


class VenvInitCommand(Command):
    """Initialize a virtual environment for the project."""

    name = "venv-init"
    help = "Initialize project virtual environment"

    def run(
        self,
        python: Optional[str] = None,
        recreate: bool = False,
    ) -> int:
        """
        Initialize a virtual environment.

        Args:
            python: Python executable to use (overrides config)
            recreate: Whether to recreate the venv if it exists

        Returns:
            Exit code (0 for success)
        """
        venv_dir = self.app.get_venv_dir()
        python_cmd = python or self.app.config.default_python

        self.app.logger.info(
            f"Initializing venv at {venv_dir} with {python_cmd}",
            prefix="venv",
        )

        # Check if venv already exists
        if venv_dir.exists():
            if recreate:
                self.app.logger.info(
                    f"Removing existing venv at {venv_dir}",
                    prefix="venv",
                )
                if not self.app.dry_run:
                    shutil.rmtree(venv_dir)
            else:
                self.app.logger.info(
                    f"Venv already exists at {venv_dir} (use --recreate to recreate)",
                    prefix="venv",
                )
                return 0

        # Create venv
        if self.app.dry_run:
            self.app.logger.info(
                f"(dry-run) Would create venv with: {python_cmd} -m venv {venv_dir}",
                prefix="venv",
            )
            return 0

        try:
            # Try to create venv
            result = subprocess.run(
                [python_cmd, "-m", "venv", str(venv_dir)],
                capture_output=True,
                text=True,
                cwd=self.app.project_root,
                shell=False,
            )

            if result.returncode != 0:
                self.app.logger.error(
                    f"Failed to create venv: {result.stderr}",
                    prefix="venv",
                )
                return result.returncode

            self.app.logger.info(
                f"Successfully created venv at {venv_dir}",
                prefix="venv",
            )

            # Upgrade pip
            self.app.logger.info("Upgrading pip...", prefix="venv")
            pip_upgrade_result = self._run_in_venv(
                venv_dir,
                ["-m", "pip", "install", "--upgrade", "pip"],
            )

            if pip_upgrade_result != 0:
                self.app.logger.warning(
                    "Failed to upgrade pip, but venv was created",
                    prefix="venv",
                )

            return 0

        except FileNotFoundError:
            self.app.logger.error(
                f"Python executable not found: {python_cmd}",
                prefix="venv",
            )
            return 127
        except Exception as e:
            self.app.logger.error(
                f"Error creating venv: {e}",
                prefix="venv",
            )
            return 1

    def _run_in_venv(self, venv_dir: Path, args: list[str]) -> int:
        """Run a command inside the venv."""
        python_path = self._get_venv_python(venv_dir)
        result = subprocess.run(
            [str(python_path)] + args,
            capture_output=True,
            text=True,
            cwd=self.app.project_root,
            shell=False,
        )
        return result.returncode

    def _get_venv_python(self, venv_dir: Path) -> Path:
        """Get the path to the Python executable inside the venv."""
        if sys.platform == "win32":
            return venv_dir / "Scripts" / "python.exe"
        else:
            return venv_dir / "bin" / "python"
