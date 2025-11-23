"""CLI entrypoint for devflow using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer

import devflow
from devflow.app import AppContext

app = typer.Typer(
    name="devflow",
    help="A Python-native project operations CLI",
    add_completion=True,
)


# Global state for the app context
_app_context: Optional[AppContext] = None


def get_app_context() -> AppContext:
    """Get the global app context."""
    if _app_context is None:
        raise RuntimeError("App context not initialized")
    return _app_context


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        typer.echo(f"devflow version {devflow.__version__}")
        raise typer.Exit()


@app.callback()
def main(
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to configuration file"),
    ] = None,
    project_root: Annotated[
        Optional[Path],
        typer.Option("--project-root", help="Path to project root"),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option(
            "--verbose",
            "-v",
            count=True,
            help="Increase verbosity (can be repeated: -v, -vv)",
        ),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress non-error output"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be done without doing it"),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
):
    """
    devflow - A Python-native project operations CLI.

    Replaces per-project shell scripts with a unified, configurable tool.
    """
    global _app_context
    _app_context = AppContext.create(
        config_path=config,
        project_root=project_root,
        verbose=verbose,
        quiet=quiet,
        dry_run=dry_run,
    )


# Stub commands
@app.command()
def venv(
    ctx: typer.Context,
):
    """Manage project virtual environment."""
    app_ctx = get_app_context()
    app_ctx.logger.info("venv command (not yet implemented)")
    typer.echo("venv command - coming soon")


@app.command()
def deps(
    ctx: typer.Context,
):
    """Manage dependencies (sync, freeze)."""
    app_ctx = get_app_context()
    app_ctx.logger.info("deps command (not yet implemented)")
    typer.echo("deps command - coming soon")


@app.command()
def test(
    ctx: typer.Context,
):
    """Run tests."""
    app_ctx = get_app_context()
    app_ctx.logger.info("test command (not yet implemented)")
    typer.echo("test command - coming soon")


@app.command()
def build(
    ctx: typer.Context,
):
    """Build distribution artifacts."""
    app_ctx = get_app_context()
    app_ctx.logger.info("build command (not yet implemented)")
    typer.echo("build command - coming soon")


@app.command()
def publish(
    ctx: typer.Context,
):
    """Build and upload to package index."""
    app_ctx = get_app_context()
    app_ctx.logger.info("publish command (not yet implemented)")
    typer.echo("publish command - coming soon")


@app.command()
def git(
    ctx: typer.Context,
):
    """Git-related helper commands."""
    app_ctx = get_app_context()
    app_ctx.logger.info("git command (not yet implemented)")
    typer.echo("git command - coming soon")


@app.command()
def task(
    ctx: typer.Context,
    name: str = typer.Argument(help="Name of the task to run"),
):
    """Run custom tasks defined in config."""
    app_ctx = get_app_context()
    app_ctx.logger.info(f"task command for '{name}' (not yet implemented)")
    typer.echo(f"task '{name}' - coming soon")


if __name__ == "__main__":
    app()
