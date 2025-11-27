"""Tests for Command base class and CommandRegistry.

Ownership: Workstream B (task/registry)
"""

import pytest

from devflow.commands.base import Command, CommandRegistry


class MockAppContext:
    """Mock AppContext for testing (real one is owned by Workstream A)."""

    def __init__(self):
        self.project_root = None
        self.config = {}
        self.dry_run = False
        self.verbosity = 0


class TestCommand:
    """Tests for the Command abstract base class."""

    def test_command_is_abstract(self):
        """Command cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Command(MockAppContext())  # type: ignore[abstract]

    def test_command_subclass_must_implement_run(self):
        """Subclasses must implement the run method."""

        class IncompleteCommand(Command):
            name = "incomplete"
            help = "An incomplete command"
            # Missing run() implementation

        with pytest.raises(TypeError):
            IncompleteCommand(MockAppContext())

    def test_command_subclass_with_run(self):
        """Complete subclasses can be instantiated."""

        class CompleteCommand(Command):
            name = "complete"
            help = "A complete command"

            def run(self, **kwargs):
                return 0

        app = MockAppContext()
        cmd = CompleteCommand(app)
        assert cmd.name == "complete"
        assert cmd.help == "A complete command"
        assert cmd.app is app

    def test_command_run_returns_exit_code(self):
        """The run method should return an exit code."""

        class ExitCodeCommand(Command):
            name = "exit"
            help = "Returns exit code"

            def run(self, exit_code: int = 0, **kwargs):
                return exit_code

        cmd = ExitCodeCommand(MockAppContext())
        assert cmd.run() == 0
        assert cmd.run(exit_code=1) == 1
        assert cmd.run(exit_code=42) == 42


class TestCommandRegistry:
    """Tests for the CommandRegistry."""

    def test_registry_starts_empty(self):
        """A new registry should have no commands."""
        registry = CommandRegistry()
        assert len(registry) == 0
        assert registry.list_commands() == []

    def test_register_command(self):
        """Commands can be registered by class."""

        class TestCmd(Command):
            name = "test"
            help = "Test command"

            def run(self, **kwargs):
                return 0

        registry = CommandRegistry()
        registry.register(TestCmd)

        assert "test" in registry
        assert len(registry) == 1
        assert registry.get("test") is TestCmd

    def test_register_duplicate_raises(self):
        """Registering a command with an existing name raises ValueError."""

        class TestCmd1(Command):
            name = "duplicate"
            help = "First"

            def run(self, **kwargs):
                return 0

        class TestCmd2(Command):
            name = "duplicate"
            help = "Second"

            def run(self, **kwargs):
                return 0

        registry = CommandRegistry()
        registry.register(TestCmd1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(TestCmd2)

    def test_get_nonexistent_returns_none(self):
        """Getting a non-existent command returns None."""
        registry = CommandRegistry()
        assert registry.get("nonexistent") is None

    def test_unregister_command(self):
        """Commands can be unregistered."""

        class TestCmd(Command):
            name = "removable"
            help = "Removable command"

            def run(self, **kwargs):
                return 0

        registry = CommandRegistry()
        registry.register(TestCmd)

        assert "removable" in registry
        assert registry.unregister("removable") is True
        assert "removable" not in registry

    def test_unregister_nonexistent_returns_false(self):
        """Unregistering a non-existent command returns False."""
        registry = CommandRegistry()
        assert registry.unregister("nonexistent") is False

    def test_list_commands_sorted(self):
        """list_commands returns sorted command names."""

        class CmdA(Command):
            name = "alpha"
            help = "Alpha"

            def run(self, **kwargs):
                return 0

        class CmdB(Command):
            name = "beta"
            help = "Beta"

            def run(self, **kwargs):
                return 0

        class CmdC(Command):
            name = "charlie"
            help = "Charlie"

            def run(self, **kwargs):
                return 0

        registry = CommandRegistry()
        registry.register(CmdC)
        registry.register(CmdA)
        registry.register(CmdB)

        assert registry.list_commands() == ["alpha", "beta", "charlie"]

    def test_contains(self):
        """The 'in' operator works correctly."""

        class TestCmd(Command):
            name = "exists"
            help = "Exists"

            def run(self, **kwargs):
                return 0

        registry = CommandRegistry()
        assert "exists" not in registry
        registry.register(TestCmd)
        assert "exists" in registry
