"""CLI entry point for devflow."""

from pathlib import Path
from typing import List, Optional

import typer
from typing_extensions import Annotated

from devflow import __version__
from devflow.app import AppContext
from devflow.commands.build import build_command
from devflow.commands.publish import publish_command
from devflow.commands.test import test_command

# Create main app
app = typer.Typer(
    name="devflow",
    help="A Python-native project operations CLI",
    add_completion=True,
)

# Global options (will be passed via context)
@app.callback()
def main(
    ctx: typer.Context,
    config: Annotated[
        Optional[Path],
        typer.Option("--config", help="Path to config file"),
    ] = None,
    project_root: Annotated[
        Optional[Path],
        typer.Option("--project-root", help="Path to project root"),
    ] = None,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase verbosity"),
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output"),
    ] = False,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Show what would be done without doing it"),
    ] = False,
    version: Annotated[
        bool,
        typer.Option("--version", help="Show version and exit"),
    ] = False,
):
    """
    devflow - A Python-native project operations CLI

    Global flags can be used with any command.
    """
    if version:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit(0)

    # Store global options in context for subcommands
    ctx.obj = {
        "config": config,
        "project_root": project_root,
        "verbose": verbose,
        "quiet": quiet,
        "dry_run": dry_run,
    }


@app.command()
def test(
    ctx: typer.Context,
    args: Annotated[
        Optional[List[str]],
        typer.Argument(help="Arguments to pass to test runner"),
    ] = None,
):
    """
    Run tests using configured test runner.

    Examples:
        devflow test
        devflow test -- -v -k test_foo
        devflow test -- --cov=mypackage
    """
    try:
        app_ctx = AppContext(
            project_root=ctx.obj["project_root"],
            config_path=ctx.obj["config"],
            verbosity=ctx.obj["verbose"],
            quiet=ctx.obj["quiet"],
            dry_run=ctx.obj["dry_run"],
        )
        exit_code = test_command(app_ctx, args=args)
        raise typer.Exit(code=exit_code)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def build(
    ctx: typer.Context,
    no_clean: Annotated[
        bool,
        typer.Option("--no-clean", help="Don't clean dist directory before building"),
    ] = False,
):
    """
    Build distribution artifacts using configured build backend.

    Examples:
        devflow build
        devflow build --no-clean
    """
    try:
        app_ctx = AppContext(
            project_root=ctx.obj["project_root"],
            config_path=ctx.obj["config"],
            verbosity=ctx.obj["verbose"],
            quiet=ctx.obj["quiet"],
            dry_run=ctx.obj["dry_run"],
        )
        exit_code = build_command(app_ctx, clean=not no_clean)
        raise typer.Exit(code=exit_code)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


@app.command()
def publish(
    ctx: typer.Context,
    repository: Annotated[
        Optional[str],
        typer.Option("--repository", "-r", help="Package repository to upload to"),
    ] = None,
    skip_tests: Annotated[
        bool,
        typer.Option("--skip-tests", help="Skip running tests before publish"),
    ] = False,
    allow_dirty: Annotated[
        bool,
        typer.Option("--allow-dirty", help="Allow dirty working tree"),
    ] = False,
    skip_existing: Annotated[
        bool,
        typer.Option("--skip-existing", help="Skip files that already exist on server"),
    ] = False,
):
    """
    Build and publish package to package index.

    This command will:
    1. Check that working tree is clean (unless --allow-dirty)
    2. Run tests (unless --skip-tests)
    3. Build the package
    4. Upload to the specified repository via twine
    5. Create a git tag (if configured)

    Examples:
        devflow publish
        devflow publish --repository testpypi
        devflow publish --dry-run
        devflow publish --skip-tests --allow-dirty
    """
    try:
        app_ctx = AppContext(
            project_root=ctx.obj["project_root"],
            config_path=ctx.obj["config"],
            verbosity=ctx.obj["verbose"],
            quiet=ctx.obj["quiet"],
            dry_run=ctx.obj["dry_run"],
        )
        exit_code = publish_command(
            app_ctx,
            repository=repository,
            skip_tests=skip_tests,
            allow_dirty=allow_dirty,
            skip_existing=skip_existing,
        )
        raise typer.Exit(code=exit_code)
    except typer.Exit:
        raise
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1) from e


if __name__ == "__main__":
    app()
