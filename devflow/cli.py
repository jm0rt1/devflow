"""Command-line interface for devflow."""

from pathlib import Path
from typing import Optional

import typer

from devflow import __version__
from devflow.app import AppContext, CommandRegistry
from devflow.config.loader import load_config
from devflow.plugins import load_plugins


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
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        help="Path to config file",
        exists=True,
    ),
    project_root: Optional[Path] = typer.Option(
        None,
        "--project-root",
        help="Project root directory",
        exists=True,
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        help="Increase verbosity (-v, -vv, etc.)",
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet",
        "-q",
        help="Suppress non-error output",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show what would be done without executing",
    ),
) -> None:
    """Global options for devflow commands."""
    # Determine project root
    if project_root is None:
        project_root = Path.cwd()
    
    # Load configuration
    loaded_config = load_config(project_root, config)
    
    # Create application context
    app_context = AppContext(
        project_root=project_root,
        config=loaded_config,
        verbose=verbose,
        quiet=quiet,
        dry_run=dry_run,
    )
    
    # Create command registry
    registry = CommandRegistry()
    app_context.command_registry = registry
    
    # Load plugins
    load_plugins(app_context)
    
    # Store context for subcommands
    ctx.obj = app_context


@app.command()
def plugin_list(ctx: typer.Context) -> None:
    """List all loaded plugins and registered commands."""
    app_context: AppContext = ctx.obj
    
    if app_context.command_registry:
        commands = app_context.command_registry.list_commands()
        if commands:
            typer.echo("Registered commands:")
            for cmd in commands:
                typer.echo(f"  - {cmd}")
        else:
            typer.echo("No commands registered")
    else:
        typer.echo("No command registry available")


if __name__ == "__main__":
    app()
