"""Test command implementation."""

from typing import List, Optional

from devflow.app import AppContext
from devflow.core.paths import get_venv_executable


def test_command(
    app: AppContext,
    args: Optional[List[str]] = None,
) -> int:
    """
    Run tests using configured test runner.

    Args:
        app: Application context
        args: Optional arguments to pass through to test runner

    Returns:
        Exit code from test runner
    """
    phase = "test"

    # Check if venv exists
    if not app.venv_exists():
        app.logger.error(
            f"Virtual environment not found at {app.venv_dir}. "
            "Run 'devflow venv init' first.",
            phase=phase,
        )
        return 1

    # Get test runner from config
    test_runner = app.config.test_runner
    app.logger.info(f"Running tests with {test_runner}", phase=phase)

    # Build command
    # Check if test_runner is configured as a task
    if test_runner in app.config.tasks:
        task_config = app.config.tasks[test_runner]
        if task_config.command:
            test_runner = task_config.command
            # Merge configured args with passed args
            base_args = task_config.args or []
            args = base_args + (args or [])

    # Get executable from venv
    try:
        test_executable = get_venv_executable(app.venv_dir, test_runner)
        if not test_executable.exists():
            # Try running as module (e.g., pytest might be in Scripts but we need pytest)
            # Fall back to python -m
            app.logger.debug(
                f"Executable {test_executable} not found, trying python -m {test_runner}",
                phase=phase,
            )
            venv_python = get_venv_executable(app.venv_dir, "python")
            cmd = [str(venv_python), "-m", test_runner] + (args or [])
        else:
            cmd = [str(test_executable)] + (args or [])
    except Exception as e:
        app.logger.error(f"Failed to find test executable: {e}", phase=phase)
        return 1

    # Run tests
    try:
        result = app.runner.run(cmd, phase=phase, check=False)
        return result.returncode
    except Exception as e:
        app.logger.error(f"Failed to run tests: {e}", phase=phase)
        return 1
