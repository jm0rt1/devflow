"""Tests for command registry."""


from devflow.commands.base import Command, CommandRegistry


class DummyCommand(Command):
    """Dummy command for testing."""

    name = "dummy"
    help = "A dummy command"

    def run(self, **kwargs) -> int:
        return 0


class AnotherCommand(Command):
    """Another dummy command for testing."""

    name = "another"
    help = "Another command"

    def run(self, **kwargs) -> int:
        return 42


def test_registry_register_and_get():
    """Test registering and retrieving commands."""
    registry = CommandRegistry()

    registry.register(DummyCommand)
    registry.register(AnotherCommand)

    assert registry.get("dummy") == DummyCommand
    assert registry.get("another") == AnotherCommand
    assert registry.get("nonexistent") is None


def test_registry_list_commands():
    """Test listing all commands."""
    registry = CommandRegistry()

    registry.register(DummyCommand)
    registry.register(AnotherCommand)

    commands = registry.list_commands()
    assert commands == ["another", "dummy"]  # Sorted alphabetically
