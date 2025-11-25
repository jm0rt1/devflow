"""Build command implementation for devflow.

This module implements `devflow build` defaulting to `python -m build` with
configurable backend (hatchling, poetry-build, etc.) and configurable dist
directory cleanup behavior.

Ownership: Workstream D
- Plugs into task engine and venv helpers
- Does not redefine config models, task execution, or git helpers
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Protocol

    class AppContextProtocol(Protocol):
        """Protocol for AppContext to avoid circular imports."""

        project_root: Path
        config: Any
        dry_run: bool
        verbose: int
        quiet: bool

        def get_venv_python(self) -> Path | None:
            """Get the python executable from the configured venv."""
            ...


@dataclass
class BuildConfig:
    """Configuration for the build command.

    Loaded from [tool.devflow] or [tool.devflow.tasks.build] in config.
    """

    backend: str = "build"  # "build", "hatchling", "poetry-build", "flit"
    args: list[str] = field(default_factory=list)
    use_venv: bool = True
    env: dict[str, str] = field(default_factory=dict)
    clean_dist: bool = True  # Whether to clean dist directory before build
    dist_dir: str = "dist"


def get_build_config(config: Any) -> BuildConfig:
    """Extract build configuration from the app config.

    Args:
        config: The loaded devflow configuration object.

    Returns:
        BuildConfig with appropriate settings.
    """
    # Get top-level settings
    build_backend = getattr(config, "build_backend", "build")

    # Get paths config for dist_dir
    paths = getattr(config, "paths", None)
    dist_dir = "dist"
    if paths:
        if isinstance(paths, dict):
            dist_dir = paths.get("dist_dir", "dist")
        else:
            dist_dir = getattr(paths, "dist_dir", "dist")

    # Try to get from tasks.build
    tasks = getattr(config, "tasks", {})
    build_task = tasks.get("build", {}) if isinstance(tasks, dict) else {}

    if isinstance(build_task, dict):
        return BuildConfig(
            backend=build_task.get("backend", build_backend),
            args=build_task.get("args", []),
            use_venv=build_task.get("use_venv", True),
            env=build_task.get("env", {}),
            clean_dist=build_task.get("clean_dist", True),
            dist_dir=build_task.get("dist_dir", dist_dir),
        )

    return BuildConfig(backend=build_backend, dist_dir=dist_dir)


def build_build_command(build_config: BuildConfig, python_path: str = "python") -> list[str]:
    """Build the build command with all arguments.

    Args:
        build_config: The build configuration.
        python_path: Path to the Python executable to use.

    Returns:
        A list of command arguments ready for subprocess execution.
    """
    backend = build_config.backend

    if backend == "build":
        # Standard python -m build
        cmd = [python_path, "-m", "build"]
    elif backend == "hatchling":
        # Hatchling backend
        cmd = [python_path, "-m", "hatchling", "build"]
    elif backend == "poetry-build":
        # Poetry build
        cmd = ["poetry", "build"]
    elif backend == "flit":
        # Flit build
        cmd = [python_path, "-m", "flit", "build"]
    else:
        # Custom backend - assume it's a module that can be run with -m
        cmd = [python_path, "-m", backend]

    cmd.extend(build_config.args)
    return cmd


def clean_dist_directory(project_root: Path, dist_dir: str, dry_run: bool, verbose: int) -> bool:
    """Clean the distribution directory before building.

    Args:
        project_root: The project root directory.
        dist_dir: The distribution directory name/path.
        dry_run: If True, only log what would be done.
        verbose: Verbosity level.

    Returns:
        True if successful, False otherwise.
    """
    dist_path = project_root / dist_dir

    if not dist_path.exists():
        if verbose > 0:
            print(f"[build] Dist directory does not exist: {dist_path}")
        return True

    if verbose > 0:
        print(f"[build] Cleaning dist directory: {dist_path}")

    if dry_run:
        print(f"[build] Would remove: {dist_path}")
        return True

    try:
        shutil.rmtree(dist_path)
        return True
    except Exception as e:
        print(f"[build] Error cleaning dist directory: {e}", file=sys.stderr)
        return False


def run_build(
    app: AppContextProtocol,
    no_clean: bool = False,
    extra_args: list[str] | None = None,
) -> int:
    """Run the build using the configured build backend.

    This function respects venv enforcement and dry-run mode.

    Args:
        app: The application context with config, project root, etc.
        no_clean: If True, skip cleaning the dist directory before building.
        extra_args: Additional arguments to pass through to the build backend.

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    build_config = get_build_config(app.config)

    # Clean dist directory if configured and not disabled
    if build_config.clean_dist and not no_clean:
        if not clean_dist_directory(
            app.project_root, build_config.dist_dir, app.dry_run, app.verbose
        ):
            return 1

    # Determine Python path
    python_path = "python"
    if build_config.use_venv:
        venv_python = app.get_venv_python()
        if venv_python and venv_python.exists():
            python_path = str(venv_python)

    # Build command
    cmd = build_build_command(build_config, python_path)
    if extra_args:
        cmd.extend(extra_args)

    # Build environment
    env = dict(build_config.env) if build_config.env else None

    # Log what we're doing
    cmd_str = " ".join(cmd)
    if app.verbose > 0:
        print(f"[build] Running: {cmd_str}")
        if env:
            print(f"[build] Environment overrides: {env}")

    if app.dry_run:
        print(f"[build] Would run: {cmd_str}")
        return 0

    # Execute the build command
    try:
        result = subprocess.run(
            cmd,
            cwd=app.project_root,
            env={**os.environ, **env} if env else None,
            check=False,
        )
        if result.returncode == 0 and app.verbose >= 0 and not app.quiet:
            # List built artifacts
            dist_path = app.project_root / build_config.dist_dir
            if dist_path.exists():
                artifacts = list(dist_path.iterdir())
                if artifacts:
                    print(f"[build] Built artifacts in {build_config.dist_dir}/:")
                    for artifact in artifacts:
                        print(f"  - {artifact.name}")
        return result.returncode
    except FileNotFoundError as e:
        print(f"[build] Error: Build tool not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[build] Error running build: {e}", file=sys.stderr)
        return 1


# Typer command registration (if Typer is available)
def register_build_command(app_typer: Any, get_app_context: Any) -> None:
    """Register the build command with the Typer app.

    This function is called by the CLI module to register the build command.

    Args:
        app_typer: The Typer application instance.
        get_app_context: A callable that returns the AppContext.
    """
    try:
        import typer
    except ImportError:
        return

    @app_typer.command()
    def build(
        no_clean: bool = typer.Option(
            False,
            "--no-clean",
            help="Skip cleaning the dist directory before building",
        ),
        args: list[str] = typer.Argument(
            None,
            help="Additional arguments to pass to the build backend",
        ),
    ) -> None:
        """Build distribution artifacts (wheel and sdist).

        By default uses `python -m build`, but can be configured to use
        hatchling, poetry-build, flit, etc. The dist directory is cleaned
        before building unless --no-clean is specified.

        Examples:
            devflow build
            devflow build --no-clean
            devflow build -- --no-isolation
        """
        ctx = get_app_context()
        exit_code = run_build(ctx, no_clean, args)
        raise typer.Exit(code=exit_code)
