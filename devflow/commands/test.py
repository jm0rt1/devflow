"""Test command implementation for devflow.

This module implements `devflow test` with pass-through args to the configured
test runner (pytest by default, but allows unittest, tox, etc.) with venv enforcement.

Ownership: Workstream D
- Plugs into task engine and venv/git helpers
- Does not redefine config models, task execution, or git helpers
"""

from __future__ import annotations

import os
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
class RunnerTestConfig:
    """Configuration for the test command.

    Loaded from [tool.devflow] or [tool.devflow.tasks.test] in config.
    """

    runner: str = "pytest"
    args: list[str] = field(default_factory=list)
    use_venv: bool = True
    env: dict[str, str] = field(default_factory=dict)


def get_test_config(config: Any) -> RunnerTestConfig:
    """Extract test configuration from the app config.

    Args:
        config: The loaded devflow configuration object.

    Returns:
        RunnerTestConfig with appropriate settings.
    """
    # Try to get from tasks.test first, then fall back to top-level test_runner
    test_runner = getattr(config, "test_runner", "pytest")
    tasks = getattr(config, "tasks", {})
    test_task = tasks.get("test", {}) if isinstance(tasks, dict) else {}

    if isinstance(test_task, dict):
        return RunnerTestConfig(
            runner=test_task.get("command", test_runner),
            args=test_task.get("args", []),
            use_venv=test_task.get("use_venv", True),
            env=test_task.get("env", {}),
        )

    return RunnerTestConfig(runner=test_runner)


def build_test_command(
    test_config: RunnerTestConfig,
    pattern: str | None = None,
    marker: str | None = None,
    cov: str | None = None,
    extra_args: list[str] | None = None,
) -> list[str]:
    """Build the test command with all arguments.

    Args:
        test_config: The test configuration.
        pattern: Test file/function pattern to match (passed to -k for pytest).
        marker: Marker expression to filter tests (passed to -m for pytest).
        cov: Coverage target (passed to --cov for pytest).
        extra_args: Additional arguments to pass through to the test runner.

    Returns:
        A list of command arguments ready for subprocess execution.
    """
    cmd = [test_config.runner]
    cmd.extend(test_config.args)

    # Handle pytest-specific flags
    if test_config.runner in ("pytest", "py.test"):
        if pattern:
            cmd.extend(["-k", pattern])
        if marker:
            cmd.extend(["-m", marker])
        if cov:
            cmd.extend(["--cov", cov])
    elif test_config.runner == "unittest":
        # For unittest, pattern is used differently
        if pattern:
            cmd.extend(["-p", pattern])
    elif test_config.runner == "tox":
        # For tox, pass args after --
        if extra_args:
            cmd.append("--")

    if extra_args:
        cmd.extend(extra_args)

    return cmd


def run_test(
    app: AppContextProtocol,
    pattern: str | None = None,
    marker: str | None = None,
    cov: str | None = None,
    extra_args: list[str] | None = None,
) -> int:
    """Run tests using the configured test runner.

    This function respects venv enforcement and dry-run mode.

    Args:
        app: The application context with config, project root, etc.
        pattern: Test file/function pattern to match.
        marker: Marker expression to filter tests.
        cov: Coverage target.
        extra_args: Additional arguments to pass through to the test runner.

    Returns:
        Exit code from the test runner (0 for success, non-zero for failure).
    """
    test_config = get_test_config(app.config)
    cmd = build_test_command(test_config, pattern, marker, cov, extra_args)

    # Determine the Python/executable to use
    executable = cmd[0]
    if test_config.use_venv:
        venv_python = app.get_venv_python()
        if venv_python and venv_python.exists():
            # Run test runner through venv python if it's a Python module
            if executable in ("pytest", "py.test", "unittest"):
                if executable == "unittest":
                    cmd = [str(venv_python), "-m", "unittest"] + cmd[1:]
                else:
                    cmd = [str(venv_python), "-m", "pytest"] + cmd[1:]
            else:
                # For other runners like tox, look in venv bin
                venv_bin = venv_python.parent
                runner_path = venv_bin / executable
                if runner_path.exists():
                    cmd[0] = str(runner_path)

    # Build environment
    env = dict(test_config.env) if test_config.env else {}

    # Log what we're doing
    cmd_str = " ".join(cmd)
    if app.verbose > 0:
        print(f"[test] Running: {cmd_str}")
        if env:
            print(f"[test] Environment overrides: {env}")

    if app.dry_run:
        print(f"[test] Would run: {cmd_str}")
        return 0

    # Execute the test command
    try:
        result = subprocess.run(
            cmd,
            cwd=app.project_root,
            env={**os.environ, **env} if env else None,
            check=False,
        )
        return result.returncode
    except FileNotFoundError as e:
        print(f"[test] Error: Test runner not found: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"[test] Error running tests: {e}", file=sys.stderr)
        return 1


# Typer command registration (if Typer is available)
def register_test_command(app_typer: Any, get_app_context: Any) -> None:
    """Register the test command with the Typer app.

    This function is called by the CLI module to register the test command.

    Args:
        app_typer: The Typer application instance.
        get_app_context: A callable that returns the AppContext.
    """
    try:
        import typer
    except ImportError:
        return

    @app_typer.command()
    def test(
        pattern: str = typer.Option(
            None,
            "--pattern",
            "-k",
            help="Test pattern to match (pytest -k)",
        ),
        marker: str = typer.Option(
            None,
            "--marker",
            "-m",
            help="Marker expression to filter tests (pytest -m)",
        ),
        cov: str = typer.Option(
            None,
            "--cov",
            help="Enable coverage for the specified module",
        ),
        args: list[str] = typer.Argument(
            None,
            help="Additional arguments to pass to the test runner",
        ),
    ) -> None:
        """Run tests using the configured test runner.

        By default uses pytest, but can be configured to use unittest, tox, etc.
        Tests are run inside the project's virtual environment.

        Examples:
            devflow test
            devflow test --pattern test_api
            devflow test --marker slow
            devflow test --cov mypackage
            devflow test -- -x --tb=short
        """
        ctx = get_app_context()
        exit_code = run_test(ctx, pattern, marker, cov, args)
        raise typer.Exit(code=exit_code)
