"""
Unit tests for the devflow package.

These tests verify basic package functionality.
"""

import devflow
from devflow import cli


class TestPackage:
    """Tests for package metadata and basic functionality."""

    def test_version_exists(self) -> None:
        """Test that version is defined."""
        assert hasattr(devflow, "__version__")
        assert devflow.__version__ == "0.1.0"

    def test_cli_main_returns_zero(self) -> None:
        """Test that CLI main returns success exit code."""
        result = cli.main()
        assert result == 0


class TestCLI:
    """Tests for CLI entry point."""

    def test_main_function_exists(self) -> None:
        """Test that main function exists and is callable."""
        assert callable(cli.main)

    def test_cli_module_can_be_run_as_main(self) -> None:
        """Test that the CLI module has __main__ guard."""
        # This verifies the module has the if __name__ == "__main__" block
        import ast

        with open(cli.__file__, encoding="utf-8") as f:
            tree = ast.parse(f.read())

        # Check for if __name__ == "__main__": pattern
        has_main_guard = any(
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Compare)
            and any(
                isinstance(comp, ast.Constant) and comp.value == "__main__"
                for comp in node.test.comparators
            )
            for node in ast.walk(tree)
        )
        assert has_main_guard, "CLI module should have __main__ guard"
