"""CLI entry point for devflow."""

from typing import Optional

import typer

from devflow import __version__

app = typer.Typer(
    name="devflow",
    help="A Python-native project operations CLI",
    no_args_is_help=True,
)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity (can be repeated)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress output except errors",
    ),
    config: Optional[str] = typer.Option(
        None,
        "--config",
        help="Path to config file",
    ),
    project_root: Optional[str] = typer.Option(
        None,
        "--project-root",
        help="Path to project root",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without doing it",
    ),
) -> None:
    """devflow - A Python-native project operations CLI."""
    # Global options are processed here
    # These will be available to all subcommands through the context
    pass


@app.command()
def version_cmd() -> None:
    """Show version information."""
    typer.echo(f"devflow version {__version__}")


if __name__ == "__main__":
    app()
