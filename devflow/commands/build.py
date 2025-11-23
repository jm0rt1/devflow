"""Build command."""

from devflow.commands.base import Command


class BuildCommand(Command):
    """Build distribution artifacts."""

    name = "build"
    help = "Build distribution artifacts"

    def run(self, **kwargs) -> int:
        """
        Execute build.
        
        Args:
            **kwargs: Additional build arguments
            
        Returns:
            Exit code
        """
        self.app.logger.info(
            f"Building with {self.app.config.build_backend}...",
            phase="build"
        )
        # Stub implementation
        return 0
