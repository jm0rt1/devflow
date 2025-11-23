"""CLI entry point for devflow."""

import sys
from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from devflow import __version__
from devflow.app import AppContext
from devflow.commands.custom import TaskCommand

# Create the main Typer app
app = typer.Typer(
    name="devflow",
    help="A Python-native project operations CLI",
    add_completion=False,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version"),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to config file"),
    ] = None,
    project_root: Annotated[
        Optional[Path],
        typer.Option("--project-root", help="Project root directory"),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase verbosity (can be repeated)"),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be done without doing it"),
    ] = False,
) -> None:
    """
    devflow - A Python-native project operations CLI.

    Global options can be used with any command.
    """
    # Create app context
    try:
        # Default verbosity is 1 (normal)
        verbosity = 1 + verbose if not quiet else 0

        app_context = AppContext(
            project_root=project_root,
            config_path=config,
            verbosity=verbosity,
            quiet=quiet,
            dry_run=dry_run,
        )

        # Store in context for subcommands
        ctx.obj = app_context

    except Exception as e:
        typer.echo(f"Error initializing devflow: {e}", err=True)
        raise typer.Exit(1)


@app.command()
def task(
    ctx: typer.Context,
    task_name: Annotated[str, typer.Argument(help="Name of the task to run")],
) -> None:
    """
    Run a custom task defined in configuration.

    Tasks can be single commands or pipelines of multiple tasks.
    Pipeline tasks are executed in sequence and stop at the first failure.
    """
    app_context: AppContext = ctx.obj

    cmd = TaskCommand(app_context)
    exit_code = cmd.run(task_name)

    if exit_code != 0:
        raise typer.Exit(exit_code)


def main_entry() -> None:
    """Entry point for console script."""
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\nInterrupted", err=True)
        sys.exit(130)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main_entry()
