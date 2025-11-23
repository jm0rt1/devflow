"""CLI entry point for devflow."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from devflow import __version__
from devflow.app import AppContext
from devflow.commands.deps import DepsFreezeCommand, DepsSyncCommand
from devflow.commands.venv import VenvInitCommand

# Create the main Typer app
app = typer.Typer(
    name="devflow",
    help="A Python-native project operations CLI",
    add_completion=False,
)

# Create subcommand groups
venv_app = typer.Typer(help="Manage project virtual environment")
deps_app = typer.Typer(help="Manage dependencies")

app.add_typer(venv_app, name="venv")
app.add_typer(deps_app, name="deps")


# Global options that are shared across commands
def version_callback(value: bool):
    """Show version and exit."""
    if value:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version", callback=version_callback, is_eager=True, help="Show version and exit"
        ),
    ] = None,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to config file"),
    ] = None,
    project_root: Annotated[
        Optional[Path],
        typer.Option("--project-root", help="Path to project root"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be done without doing it"),
    ] = False,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase verbosity (can be repeated)"),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output except errors"),
    ] = False,
):
    """
    devflow: A Python-native project operations CLI.

    Manage virtual environments, dependencies, building, testing, and publishing
    for Python projects with a unified interface.
    """
    # Store global options in context for subcommands to access
    ctx.obj = {
        "config": config,
        "project_root": project_root,
        "dry_run": dry_run,
        "verbose": verbose,
        "quiet": quiet,
    }


def _create_app_context(ctx: typer.Context) -> AppContext:
    """Create an AppContext from the global options."""
    opts = ctx.obj
    try:
        return AppContext.create(
            project_root=opts["project_root"],
            config_path=opts["config"],
            dry_run=opts["dry_run"],
            verbosity=opts["verbose"],
            quiet=opts["quiet"],
        )
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)


# Venv commands
@venv_app.command("init")
def venv_init(
    ctx: typer.Context,
    python: Annotated[
        Optional[str],
        typer.Option("--python", help="Python executable to use"),
    ] = None,
    recreate: Annotated[
        bool,
        typer.Option("--recreate", help="Recreate venv if it already exists"),
    ] = False,
):
    """Initialize a virtual environment for the project."""
    app_ctx = _create_app_context(ctx)
    cmd = VenvInitCommand(app_ctx)
    exit_code = cmd.run(python=python, recreate=recreate)
    raise typer.Exit(exit_code)


# Deps commands
@deps_app.command("sync")
def deps_sync(ctx: typer.Context):
    """Install dependencies from requirements files."""
    app_ctx = _create_app_context(ctx)
    cmd = DepsSyncCommand(app_ctx)
    exit_code = cmd.run()
    raise typer.Exit(exit_code)


@deps_app.command("freeze")
def deps_freeze(ctx: typer.Context):
    """Freeze installed dependencies to a file."""
    app_ctx = _create_app_context(ctx)
    cmd = DepsFreezeCommand(app_ctx)
    exit_code = cmd.run()
    raise typer.Exit(exit_code)


if __name__ == "__main__":
    app()
