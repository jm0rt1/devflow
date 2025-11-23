"""Test execution command."""

from devflow.commands.base import Command


class TestCommand(Command):
    """Run tests."""

    name = "test"
    help = "Run tests"

    def run(self, **kwargs) -> int:
        """
        Execute tests.
        
        Args:
            **kwargs: Additional arguments to pass to test runner
            
        Returns:
            Exit code
        """
        self.app.logger.info(f"Running tests with {self.app.config.test_runner}...", phase="test")
        # Stub implementation
        return 0
