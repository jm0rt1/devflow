"""
CLI entry point for devflow.

This module provides the main entry point for the devflow command-line interface.
The actual command implementations are provided by other workstreams.

Workstream A (Bootstrap & App Context) owns the full implementation.
This is a minimal stub for packaging purposes only.
"""

import sys


def main() -> int:
    """
    Main entry point for the devflow CLI.

    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    # TODO: Workstream A will implement full CLI with Typer
    # This stub allows the package to be installed and CLI to be invoked
    print("devflow v0.1.0")
    print("CLI implementation pending - see Workstream A")
    print("")
    print("Available commands (to be implemented):")
    print("  venv       Manage project virtual environment")
    print("  deps       Manage dependencies (sync, freeze)")
    print("  test       Run tests")
    print("  build      Build distribution artifacts")
    print("  publish    Build & upload to package index")
    print("  git        Git-related helper commands")
    print("  task       Run custom tasks defined in config")
    print("  ci-check   Opinionated CI pipeline (if configured)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
