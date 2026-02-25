"""CLI entry point for devflow.

This module provides the main CLI interface using Typer.
It implements global flags and dispatches to subcommands.
"""

from __future__ import annotations

from pathlib import Path

import typer

from devflow import __version__
from devflow.app import (
    VERBOSITY_DEBUG,
    VERBOSITY_DEFAULT,
    VERBOSITY_QUIET,
    VERBOSITY_VERBOSE,
    AppContext,
)
from devflow.core.paths import ProjectRootNotFoundError

# Create the main Typer app
app = typer.Typer(
    name="devflow",
    help="A Python-Native Project Operations CLI",
    no_args_is_help=False,
    add_completion=True,
)

# Global state for context
_app_context: AppContext | None = None


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit()


def get_context() -> AppContext:
    """Get the current application context."""
    if _app_context is None:
        raise RuntimeError("AppContext not initialized")
    return _app_context


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file",
        exists=False,  # We handle existence check ourselves
    ),
    project_root: Path | None = typer.Option(
        None,
        "--project-root",
        "-p",
        help="Override project root directory",
        exists=False,  # We handle existence check ourselves
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity (-v for verbose, -vv for debug)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress output (only show warnings and errors)",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what would be done without executing",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
) -> None:
    """devflow - A Python-Native Project Operations CLI.

    Replace per-project shell scripts with a single, configurable CLI.
    """
    global _app_context

    # Calculate verbosity level
    if quiet:
        verbosity = VERBOSITY_QUIET
    elif verbose >= 2:
        verbosity = VERBOSITY_DEBUG
    elif verbose == 1:
        verbosity = VERBOSITY_VERBOSE
    else:
        verbosity = VERBOSITY_DEFAULT

    try:
        _app_context = AppContext.create(
            project_root=project_root,
            config_path=config,
            verbosity=verbosity,
            dry_run=dry_run,
        )
    except ProjectRootNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1) from None

    # If no command is invoked, show help with available commands
    if ctx.invoked_subcommand is None:
        _show_available_commands(ctx)


def _show_available_commands(ctx: typer.Context) -> None:
    """Show available commands and project-specific tasks."""
    typer.echo("devflow - A Python-Native Project Operations CLI")
    typer.echo()
    typer.echo("Available commands:")
    typer.echo()

    # List built-in commands
    commands = [
        ("venv", "Manage project virtual environment"),
        ("deps", "Manage dependencies (sync, freeze)"),
        ("test", "Run tests"),
        ("build", "Build distribution artifacts"),
        ("publish", "Build & upload to package index"),
        ("git", "Git-related helper commands"),
        ("task", "Run custom tasks defined in config"),
        ("version", "Show project version"),
    ]

    for cmd, desc in commands:
        typer.echo(f"  {cmd:12} {desc}")

    typer.echo()
    typer.echo("Use 'devflow <command> --help' for more information about a command.")

    # Show project-specific tasks if available
    if _app_context and _app_context.config.tasks:
        typer.echo()
        typer.echo("Project-specific tasks:")
        typer.echo()
        for task_name in _app_context.config.tasks:
            typer.echo(f"  {task_name}")


# ============================================================================
# Placeholder subcommands (implementations owned by other workstreams)
# ============================================================================

# Workstream C: Venv commands
venv_app = typer.Typer(help="Manage project virtual environment")
app.add_typer(venv_app, name="venv")


@venv_app.command("init")
def venv_init(
    python: str | None = typer.Option(
        None,
        "--python",
        help="Python interpreter to use",
    ),
    recreate: bool = typer.Option(
        False,
        "--recreate",
        help="Delete and recreate venv",
    ),
) -> None:
    """Create or initialize project virtual environment.

    Implementation owned by Workstream C.
    """
    ctx = get_context()
    ctx.log("venv init: Not yet implemented (Workstream C)", phase="venv")
    if ctx.dry_run:
        ctx.log("Would create venv", phase="venv")


# Workstream C: Deps commands
deps_app = typer.Typer(help="Manage dependencies")
app.add_typer(deps_app, name="deps")


@deps_app.command("sync")
def deps_sync() -> None:
    """Synchronize dependencies from requirements.

    Implementation owned by Workstream C.
    """
    ctx = get_context()
    ctx.log("deps sync: Not yet implemented (Workstream C)", phase="deps")


@deps_app.command("freeze")
def deps_freeze() -> None:
    """Freeze installed packages to requirements file.

    Implementation owned by Workstream C.
    """
    ctx = get_context()
    ctx.log("deps freeze: Not yet implemented (Workstream C)", phase="deps")


# Workstream D: Test command
@app.command()
def test(
    pattern: str | None = typer.Option(
        None,
        "--pattern",
        "-k",
        help="Test name pattern to match",
    ),
    marker: str | None = typer.Option(
        None,
        "--marker",
        "-m",
        help="Only run tests with given marker",
    ),
    cov: bool = typer.Option(
        False,
        "--cov",
        help="Run with coverage",
    ),
) -> None:
    """Run tests.

    Implementation owned by Workstream D.
    """
    ctx = get_context()
    ctx.log("test: Not yet implemented (Workstream D)", phase="test")


# Workstream D: Build command
@app.command()
def build() -> None:
    """Build distribution artifacts.

    Implementation owned by Workstream D.
    """
    ctx = get_context()
    ctx.log("build: Not yet implemented (Workstream D)", phase="build")


# Workstream D: Publish command
@app.command()
def publish(
    repository: str | None = typer.Option(
        None,
        "--repository",
        "-r",
        help="Target repository (pypi, testpypi, or custom)",
    ),
    skip_tests: bool = typer.Option(
        False,
        "--skip-tests",
        help="Skip running tests before publish",
    ),
    allow_dirty: bool = typer.Option(
        False,
        "--allow-dirty",
        help="Allow publishing with uncommitted changes",
    ),
) -> None:
    """Build and upload to package index.

    Implementation owned by Workstream D.
    """
    ctx = get_context()
    ctx.log("publish: Not yet implemented (Workstream D)", phase="publish")


# Workstream E: Git commands
git_app = typer.Typer(help="Git-related helper commands")
app.add_typer(git_app, name="git")


@git_app.command("status")
def git_status() -> None:
    """Show git status relevant to devflow.

    Implementation owned by Workstream E.
    """
    ctx = get_context()
    ctx.log("git status: Not yet implemented (Workstream E)", phase="git")


# Workstream E: Version command
@app.command("version")
def show_version() -> None:
    """Show project version.

    Implementation owned by Workstream E.
    """
    ctx = get_context()
    ctx.log("version: Not yet implemented (Workstream E)", phase="version")


# Workstream B: Task command
@app.command()
def task(
    name: str = typer.Argument(..., help="Name of the task to run"),
) -> None:
    """Run a custom task defined in config.

    Implementation owned by Workstream B.
    """
    ctx = get_context()
    ctx.log(f"task {name}: Not yet implemented (Workstream B)", phase="task")


# Workstream G: Completion command
@app.command()
def completion(
    shell: str = typer.Argument(
        ...,
        help="Shell to generate completion for (bash, zsh, fish)",
    ),
) -> None:
    """Generate shell completion script.

    Implementation owned by Workstream G.
    """
    ctx = get_context()
    ctx.log(f"completion {shell}: Not yet implemented (Workstream G)", phase="completion")


def cli() -> None:
    """Entry point for the devflow CLI."""
    app()


if __name__ == "__main__":
    cli()
