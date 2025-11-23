"""
Main CLI entry point for devflow.

This module provides the command-line interface using Typer.
"""

import sys
from typing import Optional

import typer
from typing_extensions import Annotated

from devflow import __version__

app = typer.Typer(
    name="devflow",
    help="A Python-Native Project Operations CLI",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit.",
        ),
    ] = None,
    config: Annotated[
        Optional[str],
        typer.Option(
            "--config",
            help="Path to config file.",
        ),
    ] = None,
    project_root: Annotated[
        Optional[str],
        typer.Option(
            "--project-root",
            help="Project root directory.",
        ),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="Show what would be done without executing.",
        ),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (can be repeated).",
        ),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option(
            "--quiet",
            "-q",
            help="Suppress output.",
        ),
    ] = False,
) -> None:
    """
    devflow - A Python-Native Project Operations CLI

    Unified CLI for managing Python project operations including venv management,
    dependency handling, testing, building, and publishing.

    Global options apply to all subcommands.
    """
    pass


@app.command()
def venv(
    action: Annotated[str, typer.Argument(help="Action: init")] = "init",
) -> None:
    """Manage project virtual environment."""
    typer.echo(f"[venv] Would execute: {action} (not yet implemented)")
    raise typer.Exit(1)


@app.command()
def deps(
    action: Annotated[str, typer.Argument(help="Action: sync, freeze")] = "sync",
) -> None:
    """Manage dependencies (sync, freeze)."""
    typer.echo(f"[deps] Would execute: {action} (not yet implemented)")
    raise typer.Exit(1)


@app.command()
def test() -> None:
    """Run tests."""
    typer.echo("[test] Would run tests (not yet implemented)")
    raise typer.Exit(1)


@app.command()
def build() -> None:
    """Build distribution artifacts."""
    typer.echo("[build] Would build package (not yet implemented)")
    raise typer.Exit(1)


@app.command()
def publish() -> None:
    """Build & upload to package index."""
    typer.echo("[publish] Would publish package (not yet implemented)")
    raise typer.Exit(1)


@app.command()
def task(
    name: Annotated[str, typer.Argument(help="Task name to execute")],
) -> None:
    """Run custom tasks defined in config."""
    typer.echo(f"[task] Would execute task '{name}' (not yet implemented)")
    raise typer.Exit(1)


def cli_main() -> None:
    """Entry point for console script."""
    try:
        app()
    except KeyboardInterrupt:
        typer.echo("\nInterrupted", err=True)
        sys.exit(130)
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli_main()
