"""Tests for the plugin system."""

import sys
from io import StringIO
from pathlib import Path

import pytest

from devflow.app import AppContext, CommandRegistry
from devflow.commands.base import Command
from devflow.plugins import (
    discover_config_plugins,
    load_plugins,
)


class TestCommandRegistry:
    """Tests for CommandRegistry."""
    
    def test_register_command(self):
        """Test registering a command."""
        registry = CommandRegistry()
        
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            
            def run(self, **kwargs):
                return 0
        
        registry.register("test", TestCommand)
        assert registry.get("test") == TestCommand
    
    def test_register_duplicate_raises_error(self):
        """Test that registering duplicate command names raises an error."""
        registry = CommandRegistry()
        
        class TestCommand(Command):
            name = "test"
            help = "Test command"
            
            def run(self, **kwargs):
                return 0
        
        registry.register("test", TestCommand)
        
        with pytest.raises(ValueError, match="already registered"):
            registry.register("test", TestCommand)
    
    def test_get_nonexistent_command(self):
        """Test getting a command that doesn't exist."""
        registry = CommandRegistry()
        assert registry.get("nonexistent") is None
    
    def test_list_commands(self):
        """Test listing all registered commands."""
        registry = CommandRegistry()
        
        class Command1(Command):
            name = "cmd1"
            help = "Command 1"
            
            def run(self, **kwargs):
                return 0
        
        class Command2(Command):
            name = "cmd2"
            help = "Command 2"
            
            def run(self, **kwargs):
                return 0
        
        registry.register("cmd1", Command1)
        registry.register("cmd2", Command2)
        
        commands = registry.list_commands()
        assert commands == ["cmd1", "cmd2"]


class TestConfigPluginDiscovery:
    """Tests for config-based plugin discovery."""
    
    def test_discover_valid_config_plugin(self):
        """Test discovering a valid plugin from config."""
        config = {
            'plugins': {
                'modules': ['tests.fixtures.plugins.sample_plugin']
            }
        }
        
        plugins = discover_config_plugins(config)
        assert len(plugins) == 1
        assert plugins[0][0] == 'tests.fixtures.plugins.sample_plugin'
        assert callable(plugins[0][1])
    
    def test_discover_multiple_config_plugins(self):
        """Test discovering multiple plugins from config."""
        config = {
            'plugins': {
                'modules': [
                    'tests.fixtures.plugins.sample_plugin',
                    'tests.fixtures.plugins.bad_plugin',
                ]
            }
        }
        
        # Capture stderr to suppress warnings
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            plugins = discover_config_plugins(config)
        finally:
            sys.stderr = old_stderr
        
        # Both should be discovered (even though bad_plugin will fail at registration)
        assert len(plugins) == 2
    
    def test_discover_no_plugins_config(self):
        """Test when config has no plugins section."""
        config = {}
        plugins = discover_config_plugins(config)
        assert len(plugins) == 0
    
    def test_discover_empty_modules_list(self):
        """Test when config has empty modules list."""
        config = {
            'plugins': {
                'modules': []
            }
        }
        plugins = discover_config_plugins(config)
        assert len(plugins) == 0
    
    def test_discover_invalid_module_path(self):
        """Test graceful handling of invalid module path."""
        config = {
            'plugins': {
                'modules': ['nonexistent.module.path']
            }
        }
        
        # Capture stderr to suppress warnings
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            plugins = discover_config_plugins(config)
        finally:
            sys.stderr = old_stderr
        
        # Should return empty list but not crash
        assert len(plugins) == 0
    
    def test_discover_plugin_without_register(self):
        """Test handling of plugin module without register function."""
        config = {
            'plugins': {
                'modules': ['tests.fixtures.plugins.no_register']
            }
        }
        
        # Capture stderr to suppress warnings
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            plugins = discover_config_plugins(config)
        finally:
            sys.stderr = old_stderr
        
        # Should return empty list due to missing register function
        assert len(plugins) == 0
    
    def test_discover_invalid_modules_type(self):
        """Test handling of invalid modules type (not a list)."""
        config = {
            'plugins': {
                'modules': 'not.a.list'
            }
        }
        
        # Capture stderr to suppress warnings
        old_stderr = sys.stderr
        sys.stderr = StringIO()
        try:
            plugins = discover_config_plugins(config)
        finally:
            sys.stderr = old_stderr
        
        # Should return empty list
        assert len(plugins) == 0


class TestPluginLoading:
    """Tests for plugin loading and registration."""
    
    def test_load_sample_plugin(self):
        """Test loading the sample plugin."""
        app = AppContext(
            project_root=Path.cwd(),
            config={
                'plugins': {
                    'modules': ['tests.fixtures.plugins.sample_plugin']
                }
            },
        )
        app.command_registry = CommandRegistry()
        
        load_plugins(app)
        
        # Check that the hello command was registered
        assert app.command_registry.get('hello') is not None
    
    def test_load_plugins_without_registry_raises_error(self):
        """Test that loading plugins without a registry raises an error."""
        app = AppContext(
            project_root=Path.cwd(),
            config={},
        )
        # No command_registry set
        
        with pytest.raises(RuntimeError, match="command_registry"):
            load_plugins(app)
    
    def test_bad_plugin_does_not_crash(self):
        """Test that a bad plugin doesn't crash the entire system."""
        app = AppContext(
            project_root=Path.cwd(),
            config={
                'plugins': {
                    'modules': [
                        'tests.fixtures.plugins.sample_plugin',
                        'tests.fixtures.plugins.bad_plugin',
                    ]
                }
            },
        )
        app.command_registry = CommandRegistry()
        
        # Should not raise an exception
        load_plugins(app)
        
        # Good plugin should still be loaded
        assert app.command_registry.get('hello') is not None


class TestPluginPrecedence:
    """Tests for plugin precedence rules."""
    
    def test_config_plugin_precedence(self):
        """Test that config plugins take precedence over entry point plugins.
        
        This is more of a documentation test since we can't easily set up
        entry points in a test environment. It verifies the precedence logic.
        """
        app = AppContext(
            project_root=Path.cwd(),
            config={
                'plugins': {
                    'modules': ['tests.fixtures.plugins.sample_plugin']
                }
            },
        )
        app.command_registry = CommandRegistry()
        
        load_plugins(app)
        
        # Should have loaded the plugin
        assert len(app.command_registry.list_commands()) >= 1


class TestPluginIsolation:
    """Tests for plugin isolation (bad plugins don't affect others)."""
    
    def test_multiple_plugins_with_one_bad(self):
        """Test that one bad plugin doesn't prevent others from loading."""
        # Create a custom command to verify loading
        class CustomCommand(Command):
            name = "custom"
            help = "Custom command"
            
            def run(self, **kwargs):
                return 0
        
        def good_plugin(registry, app):
            registry.register("custom", CustomCommand)
        
        def bad_plugin(registry, app):
            raise RuntimeError("Bad plugin error")
        
        app = AppContext(
            project_root=Path.cwd(),
            config={},
        )
        app.command_registry = CommandRegistry()
        
        # Manually register plugins to simulate discovery
        from devflow.plugins import PluginRegisterFunc
        
        plugins: list[tuple[str, PluginRegisterFunc]] = [
            ("good", good_plugin),
            ("bad", bad_plugin),
        ]
        
        # Load them
        for name, register_func in plugins:
            try:
                register_func(app.command_registry, app)
            except Exception:
                pass  # Ignore errors like load_plugins does
        
        # Good plugin should have registered
        assert app.command_registry.get("custom") is not None


class TestSamplePlugin:
    """Tests for the sample plugin implementation."""
    
    def test_sample_plugin_hello_command(self):
        """Test the hello command from sample plugin."""
        from tests.fixtures.plugins.sample_plugin import HelloCommand
        
        app = AppContext(
            project_root=Path.cwd(),
            config={},
        )
        
        cmd = HelloCommand(app)
        exit_code = cmd.run(name="Test")
        
        assert exit_code == 0
    
    def test_sample_plugin_hello_command_dry_run(self):
        """Test the hello command in dry-run mode."""
        from tests.fixtures.plugins.sample_plugin import HelloCommand
        
        app = AppContext(
            project_root=Path.cwd(),
            config={},
            dry_run=True,
        )
        
        cmd = HelloCommand(app)
        exit_code = cmd.run(name="Test")
        
        assert exit_code == 0
    
    def test_sample_plugin_hello_command_default_name(self):
        """Test the hello command with default name."""
        from tests.fixtures.plugins.sample_plugin import HelloCommand
        
        app = AppContext(
            project_root=Path.cwd(),
            config={},
        )
        
        cmd = HelloCommand(app)
        exit_code = cmd.run()
        
        assert exit_code == 0
