"""Main CLI entry point using Typer."""

from pathlib import Path
from typing import Optional

import typer
from typing_extensions import Annotated

from devflow import __version__
from devflow.app import AppContext
from devflow.commands.base import CommandRegistry
from devflow.commands.build import BuildCommand
from devflow.commands.completion import CompletionCommand
from devflow.commands.deps import DepsCommand
from devflow.commands.task import TaskCommand
from devflow.commands.test import TestCommand
from devflow.commands.venv import VenvCommand

app = typer.Typer(
    name="devflow",
    help="""
    devflow - A Python-native project operations CLI
    
    Replace per-project shell scripts with a single, configurable CLI tool.
    
    Examples:
        devflow venv init              # Create virtual environment
        devflow deps sync              # Install dependencies
        devflow test                   # Run tests
        devflow build                  # Build distribution
        devflow task lint              # Run custom task
        devflow completion bash        # Generate bash completion
    
    Configuration:
        Define tasks in pyproject.toml:
        
        [tool.devflow.tasks.lint]
        command = "ruff"
        args = ["check", "."]
        
        [tool.devflow.tasks.ci-check]
        pipeline = ["lint", "test", "build"]
    """,
    no_args_is_help=False,  # We'll handle no args ourselves
    add_completion=False,  # We provide our own completion command
)

# Global state for command registry
_registry: Optional[CommandRegistry] = None


def get_registry() -> CommandRegistry:
    """Get or create the command registry."""
    global _registry
    if _registry is None:
        _registry = CommandRegistry()
        _registry.register(VenvCommand)
        _registry.register(DepsCommand)
        _registry.register(TestCommand)
        _registry.register(BuildCommand)
        _registry.register(TaskCommand)
        _registry.register(CompletionCommand)
    return _registry


def version_callback(value: bool):
    """Handle --version flag."""
    if value:
        typer.echo(f"devflow version {__version__}")
        raise typer.Exit()


def list_commands_and_tasks(app_ctx: AppContext):
    """List available commands and project tasks."""
    typer.echo("devflow - A Python-native project operations CLI\n")
    
    typer.echo("Usage: devflow [OPTIONS] COMMAND [ARGS]...\n")
    
    typer.echo("Core Commands:")
    registry = get_registry()
    for name, help_text in registry.list_commands().items():
        typer.echo(f"  {name:15} {help_text}")
    
    # List project tasks if any are defined
    tasks = app_ctx.config.list_tasks()
    if tasks:
        typer.echo("\nProject Tasks:")
        for task_name in tasks:
            task = app_ctx.config.get_task(task_name)
            if task and task.pipeline:
                typer.echo(f"  {task_name:15} Pipeline: {', '.join(task.pipeline)}")
            elif task and task.command:
                typer.echo(f"  {task_name:15} Command: {task.command}")
            else:
                typer.echo(f"  {task_name:15} Custom task")
    
    typer.echo("\nGlobal Options:")
    typer.echo("  --config PATH       Configuration file path")
    typer.echo("  --project-root PATH Project root directory")
    typer.echo("  --dry-run          Show what would be done without executing")
    typer.echo("  -v, --verbose      Increase verbosity (can be repeated)")
    typer.echo("  -q, --quiet        Suppress output")
    typer.echo("  --version          Show version")
    typer.echo("  --help             Show this message")
    
    typer.echo("\nRun 'devflow COMMAND --help' for more information on a command.")


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    config: Annotated[
        Optional[Path],
        typer.Option(help="Configuration file path")
    ] = None,
    project_root: Annotated[
        Optional[Path],
        typer.Option(help="Project root directory")
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option(help="Show what would be done without executing")
    ] = False,
    verbose: Annotated[
        int,
        typer.Option("--verbose", "-v", count=True, help="Increase verbosity")
    ] = 0,
    quiet: Annotated[
        bool,
        typer.Option("--quiet", "-q", help="Suppress output")
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, is_eager=True, help="Show version")
    ] = None,
):
    """
    devflow - A Python-native project operations CLI
    
    Replace per-project shell scripts (build.sh, test.sh, publish.sh, etc.)
    with a single, configurable CLI tool.
    """
    # Create app context and store in Typer context
    app_ctx = AppContext(
        project_root=project_root,
        config_path=config,
        verbosity=verbose,
        quiet=quiet,
        dry_run=dry_run,
    )
    ctx.obj = app_ctx
    
    # If no subcommand was provided, list commands and tasks
    if ctx.invoked_subcommand is None:
        list_commands_and_tasks(app_ctx)
        raise typer.Exit()


@app.command()
def venv(
    ctx: typer.Context,
    subcommand: Annotated[
        str,
        typer.Argument(help="Subcommand: init")
    ] = "init",
    python: Annotated[
        Optional[str],
        typer.Option(help="Python executable or version")
    ] = None,
    recreate: Annotated[
        bool,
        typer.Option(help="Recreate virtual environment if it exists")
    ] = False,
):
    """
    Manage project virtual environment.
    
    Examples:
        devflow venv init              # Create .venv with default Python
        devflow venv init --python 3.11 # Create with specific Python version
        devflow venv init --recreate    # Recreate existing venv
    """
    app_ctx: AppContext = ctx.obj
    cmd = VenvCommand(app_ctx)
    exit_code = cmd.run(subcommand=subcommand, python=python, recreate=recreate)
    raise typer.Exit(code=exit_code)


@app.command()
def deps(
    ctx: typer.Context,
    subcommand: Annotated[
        str,
        typer.Argument(help="Subcommand: sync, freeze")
    ] = "sync",
):
    """
    Manage dependencies (sync, freeze).
    
    Examples:
        devflow deps sync              # Install dependencies
        devflow deps freeze            # Freeze dependencies to file
    """
    app_ctx: AppContext = ctx.obj
    cmd = DepsCommand(app_ctx)
    exit_code = cmd.run(subcommand=subcommand)
    raise typer.Exit(code=exit_code)


@app.command()
def test(
    ctx: typer.Context,
    args: Annotated[
        Optional[list[str]],
        typer.Argument(help="Additional arguments to pass to test runner")
    ] = None,
):
    """
    Run tests.
    
    Examples:
        devflow test                   # Run all tests
        devflow test tests/test_core.py # Run specific test file
        devflow test -v                # Run with verbose output
    """
    app_ctx: AppContext = ctx.obj
    cmd = TestCommand(app_ctx)
    exit_code = cmd.run(args=args or [])
    raise typer.Exit(code=exit_code)


@app.command()
def build(ctx: typer.Context):
    """
    Build distribution artifacts.
    
    Examples:
        devflow build                  # Build wheel and sdist
        devflow --dry-run build        # Show what would be built
    """
    app_ctx: AppContext = ctx.obj
    cmd = BuildCommand(app_ctx)
    exit_code = cmd.run()
    raise typer.Exit(code=exit_code)


@app.command()
def task(
    ctx: typer.Context,
    task_name: Annotated[
        str,
        typer.Argument(help="Name of the task to run")
    ],
):
    """
    Run custom tasks defined in config.
    
    Examples:
        devflow task lint              # Run lint task
        devflow task ci-check          # Run ci-check pipeline
    
    Define tasks in pyproject.toml:
        [tool.devflow.tasks.lint]
        command = "ruff"
        args = ["check", "."]
        
        [tool.devflow.tasks.ci-check]
        pipeline = ["lint", "test", "build"]
    """
    app_ctx: AppContext = ctx.obj
    cmd = TaskCommand(app_ctx)
    exit_code = cmd.run(task_name=task_name)
    raise typer.Exit(code=exit_code)


@app.command()
def completion(
    ctx: typer.Context,
    shell: Annotated[
        str,
        typer.Argument(help="Shell type: bash, zsh, or fish")
    ],
):
    """
    Generate shell completion script.
    
    Examples:
        devflow completion bash        # Output bash completion script
        devflow completion zsh         # Output zsh completion script
        devflow completion fish        # Output fish completion script
    
    Installation:
        # Bash
        devflow completion bash > ~/.devflow-completion.bash
        echo 'source ~/.devflow-completion.bash' >> ~/.bashrc
        
        # Or for immediate effect:
        eval "$(devflow completion bash)"
        
        # Zsh
        devflow completion zsh > ~/.devflow-completion.zsh
        echo 'source ~/.devflow-completion.zsh' >> ~/.zshrc
        
        # Fish
        devflow completion fish > ~/.config/fish/completions/devflow.fish
    """
    app_ctx: AppContext = ctx.obj
    cmd = CompletionCommand(app_ctx)
    exit_code = cmd.run(shell=shell)
    raise typer.Exit(code=exit_code)


def cli_main():
    """CLI entry point."""
    app()


if __name__ == "__main__":
    cli_main()
