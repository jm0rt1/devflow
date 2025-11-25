"""Tests for the devflow plugin system.

These tests verify:
- Plugin discovery from entry points and config
- Plugin registration with the command registry
- Precedence rules (config plugins override entry point plugins)
- Failure isolation (bad plugins don't crash the CLI)
"""

from __future__ import annotations

import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from devflow.plugins import (
    PluginError,
    PluginSpec,
    discover_config_plugins,
    discover_entry_point_plugins,
    load_all_plugins,
)
from devflow.plugins.interface import PluginMetadata
from devflow.plugins.loader import (
    PRIORITY_CONFIG,
    PRIORITY_ENTRY_POINT,
    _call_register,
    _load_plugin_module,
    _merge_plugins,
)


class TestPluginMetadata:
    """Tests for PluginMetadata class."""

    def test_metadata_creation(self) -> None:
        """Test basic metadata creation."""
        meta = PluginMetadata(
            name="test-plugin",
            module_path="test.plugin.module",
            source="entry_point",
            priority=0,
        )
        assert meta.name == "test-plugin"
        assert meta.module_path == "test.plugin.module"
        assert meta.source == "entry_point"
        assert meta.priority == 0

    def test_metadata_equality(self) -> None:
        """Test metadata equality comparison."""
        meta1 = PluginMetadata("test", "mod", "entry_point", 0)
        meta2 = PluginMetadata("test", "mod", "entry_point", 0)
        meta3 = PluginMetadata("test", "mod", "config", 0)

        assert meta1 == meta2
        assert meta1 != meta3  # Different source

    def test_metadata_repr(self) -> None:
        """Test metadata string representation."""
        meta = PluginMetadata("test", "mod", "config", 100)
        repr_str = repr(meta)
        assert "test" in repr_str
        assert "mod" in repr_str
        assert "config" in repr_str

    def test_metadata_hash(self) -> None:
        """Test metadata can be used in sets/dicts."""
        meta1 = PluginMetadata("test", "mod", "entry_point", 0)
        meta2 = PluginMetadata("test", "mod", "entry_point", 0)

        # Should be hashable and equal items should hash the same
        plugin_set = {meta1, meta2}
        assert len(plugin_set) == 1


class TestPluginError:
    """Tests for PluginError exception."""

    def test_error_creation(self) -> None:
        """Test creating a plugin error."""
        error = PluginError("my-plugin", "Something went wrong")
        assert error.plugin_name == "my-plugin"
        assert error.message == "Something went wrong"
        assert error.cause is None
        assert "my-plugin" in str(error)
        assert "Something went wrong" in str(error)

    def test_error_with_cause(self) -> None:
        """Test error with underlying cause."""
        cause = ValueError("Original error")
        error = PluginError("my-plugin", "Wrapper message", cause=cause)
        assert error.cause is cause


class TestDiscoverEntryPointPlugins:
    """Tests for entry point plugin discovery."""

    def test_discover_no_plugins(self) -> None:
        """Test discovery when no plugins are registered."""
        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = []
            plugins = discover_entry_point_plugins()
            assert plugins == []

    def test_discover_single_plugin(self) -> None:
        """Test discovery of a single entry point plugin."""
        mock_ep = MagicMock()
        mock_ep.name = "test-plugin"
        mock_ep.value = "test.plugin.module"

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep]
            plugins = discover_entry_point_plugins()

            assert len(plugins) == 1
            assert plugins[0].name == "test-plugin"
            assert plugins[0].module_path == "test.plugin.module"
            assert plugins[0].source == "entry_point"
            assert plugins[0].priority == PRIORITY_ENTRY_POINT

    def test_discover_multiple_plugins(self) -> None:
        """Test discovery of multiple entry point plugins."""
        mock_ep1 = MagicMock()
        mock_ep1.name = "plugin-a"
        mock_ep1.value = "plugin_a"

        mock_ep2 = MagicMock()
        mock_ep2.name = "plugin-b"
        mock_ep2.value = "plugin_b"

        with patch("importlib.metadata.entry_points") as mock_eps:
            mock_eps.return_value = [mock_ep1, mock_ep2]
            plugins = discover_entry_point_plugins()

            assert len(plugins) == 2
            assert {p.name for p in plugins} == {"plugin-a", "plugin-b"}


class TestDiscoverConfigPlugins:
    """Tests for config-based plugin discovery."""

    def test_discover_none(self) -> None:
        """Test discovery with no plugins in config."""
        plugins = discover_config_plugins(None)
        assert plugins == []

    def test_discover_empty_list(self) -> None:
        """Test discovery with empty plugin list."""
        plugins = discover_config_plugins([])
        assert plugins == []

    def test_discover_single_plugin(self) -> None:
        """Test discovery of a single config plugin."""
        plugins = discover_config_plugins(["my.custom.plugin"])

        assert len(plugins) == 1
        assert plugins[0].name == "plugin"  # Last component of path
        assert plugins[0].module_path == "my.custom.plugin"
        assert plugins[0].source == "config"
        assert plugins[0].priority == PRIORITY_CONFIG

    def test_discover_multiple_plugins(self) -> None:
        """Test discovery of multiple config plugins."""
        plugin_modules = ["plugin_a", "package.plugin_b", "deep.nested.plugin_c"]
        plugins = discover_config_plugins(plugin_modules)

        assert len(plugins) == 3
        assert plugins[0].name == "plugin_a"
        assert plugins[1].name == "plugin_b"
        assert plugins[2].name == "plugin_c"

    def test_priority_increases_with_index(self) -> None:
        """Test that config plugins get increasing priority."""
        plugin_modules = ["first", "second", "third"]
        plugins = discover_config_plugins(plugin_modules)

        assert plugins[0].priority == PRIORITY_CONFIG
        assert plugins[1].priority == PRIORITY_CONFIG + 1
        assert plugins[2].priority == PRIORITY_CONFIG + 2


class TestMergePlugins:
    """Tests for plugin merging and precedence."""

    def test_merge_empty_lists(self) -> None:
        """Test merging empty plugin lists."""
        result = _merge_plugins([], [])
        assert result == []

    def test_merge_only_entry_points(self) -> None:
        """Test merging with only entry point plugins."""
        ep_plugins = [
            PluginMetadata("a", "mod_a", "entry_point", 0),
            PluginMetadata("b", "mod_b", "entry_point", 0),
        ]
        result = _merge_plugins(ep_plugins, [])

        assert len(result) == 2
        assert {p.name for p in result} == {"a", "b"}

    def test_merge_only_config(self) -> None:
        """Test merging with only config plugins."""
        config_plugins = [
            PluginMetadata("x", "mod_x", "config", 100),
            PluginMetadata("y", "mod_y", "config", 101),
        ]
        result = _merge_plugins([], config_plugins)

        assert len(result) == 2
        assert {p.name for p in result} == {"x", "y"}

    def test_config_overrides_entry_point(self) -> None:
        """Test that config plugins override entry point plugins with same name."""
        ep_plugins = [
            PluginMetadata("plugin", "original.module", "entry_point", 0),
        ]
        config_plugins = [
            PluginMetadata("plugin", "override.module", "config", 100),
        ]

        result = _merge_plugins(ep_plugins, config_plugins)

        assert len(result) == 1
        assert result[0].module_path == "override.module"
        assert result[0].source == "config"

    def test_merge_preserves_unique_plugins(self) -> None:
        """Test that unique plugins from both sources are preserved."""
        ep_plugins = [
            PluginMetadata("ep-only", "ep.module", "entry_point", 0),
        ]
        config_plugins = [
            PluginMetadata("config-only", "config.module", "config", 100),
        ]

        result = _merge_plugins(ep_plugins, config_plugins)

        assert len(result) == 2
        names = {p.name for p in result}
        assert "ep-only" in names
        assert "config-only" in names

    def test_merge_sorted_by_priority(self) -> None:
        """Test that merged plugins are sorted by priority."""
        ep_plugins = [
            PluginMetadata("z", "mod_z", "entry_point", 0),
            PluginMetadata("a", "mod_a", "entry_point", 0),
        ]
        config_plugins = [
            PluginMetadata("m", "mod_m", "config", 100),
        ]

        result = _merge_plugins(ep_plugins, config_plugins)

        # Entry points (priority 0) should come before config (priority 100)
        assert result[0].priority == 0
        assert result[1].priority == 0
        assert result[2].priority == 100


class TestLoadPluginModule:
    """Tests for loading plugin modules."""

    def test_load_good_plugin(self) -> None:
        """Test loading a valid plugin module."""
        metadata = PluginMetadata(
            "sample_hello",
            "tests.fixtures.plugins.sample_hello",
            "config",
            100,
        )

        register_fn = _load_plugin_module(metadata)

        assert register_fn is not None
        assert callable(register_fn)

    def test_load_missing_module(self) -> None:
        """Test loading a non-existent module."""
        metadata = PluginMetadata(
            "nonexistent",
            "nonexistent.module.path",
            "config",
            100,
        )

        with pytest.raises(PluginError) as exc_info:
            _load_plugin_module(metadata)

        assert exc_info.value.plugin_name == "nonexistent"
        assert "Failed to import" in exc_info.value.message

    def test_load_missing_register_function(self) -> None:
        """Test loading a module without register function."""
        metadata = PluginMetadata(
            "missing_register",
            "tests.fixtures.plugins.missing_register",
            "config",
            100,
        )

        with pytest.raises(PluginError) as exc_info:
            _load_plugin_module(metadata)

        assert "no 'register' function" in exc_info.value.message

    def test_load_import_error(self) -> None:
        """Test loading a module that fails to import."""
        metadata = PluginMetadata(
            "bad_import",
            "tests.fixtures.plugins.bad_import",
            "config",
            100,
        )

        with pytest.raises(PluginError) as exc_info:
            _load_plugin_module(metadata)

        assert exc_info.value.plugin_name == "bad_import"


class TestCallRegister:
    """Tests for calling plugin register functions."""

    def test_call_successful_register(self) -> None:
        """Test calling a register function that succeeds."""
        metadata = PluginMetadata("test", "test.module", "config", 100)
        mock_fn = MagicMock()
        registry = MagicMock()
        app = MagicMock()

        _call_register(metadata, mock_fn, registry, app)

        mock_fn.assert_called_once_with(registry, app)

    def test_call_failing_register(self) -> None:
        """Test calling a register function that fails."""
        metadata = PluginMetadata("test", "test.module", "config", 100)
        mock_fn = MagicMock(side_effect=RuntimeError("Registration failed"))
        registry = MagicMock()
        app = MagicMock()

        with pytest.raises(PluginError) as exc_info:
            _call_register(metadata, mock_fn, registry, app)

        assert exc_info.value.plugin_name == "test"
        assert "Error during registration" in exc_info.value.message

    def test_call_propagates_plugin_error(self) -> None:
        """Test that PluginError from register is propagated."""
        metadata = PluginMetadata("test", "test.module", "config", 100)
        original_error = PluginError("test", "Custom error")
        mock_fn = MagicMock(side_effect=original_error)
        registry = MagicMock()
        app = MagicMock()

        with pytest.raises(PluginError) as exc_info:
            _call_register(metadata, mock_fn, registry, app)

        # Should be the same error, not wrapped
        assert exc_info.value is original_error


class TestLoadAllPlugins:
    """Tests for the main plugin loading function."""

    def test_load_no_plugins(self) -> None:
        """Test loading when no plugins are available."""
        registry = MagicMock()
        app = MagicMock()

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(registry, app, None)

        assert result.success_count == 0
        assert result.failure_count == 0

    def test_load_good_plugin(self) -> None:
        """Test loading a valid plugin from config."""
        registry = MagicMock()
        app = MagicMock()

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(
                registry, app, ["tests.fixtures.plugins.sample_hello"]
            )

        assert result.success_count == 1
        assert "sample_hello" in result.loaded
        assert result.failure_count == 0
        registry.register.assert_called_once()

    def test_load_bad_register_plugin(self) -> None:
        """Test that a plugin with bad register function doesn't crash."""
        registry = MagicMock()
        app = MagicMock()

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(
                registry, app, ["tests.fixtures.plugins.bad_register"]
            )

        assert result.success_count == 0
        assert result.failure_count == 1
        assert "bad_register" in result.failed

    def test_load_bad_import_plugin(self) -> None:
        """Test that a plugin with import error doesn't crash."""
        registry = MagicMock()
        app = MagicMock()

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(
                registry, app, ["tests.fixtures.plugins.bad_import"]
            )

        assert result.success_count == 0
        assert result.failure_count == 1

    def test_failure_isolation_multiple_plugins(self) -> None:
        """Test that one bad plugin doesn't prevent others from loading."""
        registry = MagicMock()
        app = MagicMock()

        # Load both good and bad plugins
        plugin_modules = [
            "tests.fixtures.plugins.bad_register",  # Will fail
            "tests.fixtures.plugins.sample_hello",  # Should succeed
        ]

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(registry, app, plugin_modules)

        # Good plugin should still load despite bad plugin
        assert result.success_count == 1
        assert result.failure_count == 1
        assert "sample_hello" in result.loaded

    def test_load_result_repr(self) -> None:
        """Test PluginLoadResult string representation."""
        registry = MagicMock()
        app = MagicMock()

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(
                registry, app, ["tests.fixtures.plugins.sample_hello"]
            )

        repr_str = repr(result)
        assert "sample_hello" in repr_str


class TestPluginSpec:
    """Tests for the PluginSpec protocol."""

    def test_protocol_check_valid_module(self) -> None:
        """Test that valid plugin modules satisfy the protocol."""
        import tests.fixtures.plugins.sample_hello as sample

        # The module should have a register function
        assert hasattr(sample, "register")
        assert callable(sample.register)

    def test_protocol_check_invalid_module(self) -> None:
        """Test that invalid modules don't satisfy the protocol."""
        import tests.fixtures.plugins.missing_register as bad

        # The module should not have a register function
        assert not hasattr(bad, "register")


class TestIntegration:
    """Integration tests for the plugin system."""

    def test_full_plugin_lifecycle(self) -> None:
        """Test complete plugin discovery, loading, and registration."""

        # Create a mock registry that tracks registrations
        class MockRegistry:
            def __init__(self) -> None:
                self.registered: list[Any] = []

            def register(self, cmd_cls: Any) -> None:
                self.registered.append(cmd_cls)

        # Create a mock app context
        class MockApp:
            dry_run = False
            verbose = 0

        registry = MockRegistry()
        app = MockApp()

        with patch("devflow.plugins.loader.discover_entry_point_plugins") as mock_ep:
            mock_ep.return_value = []
            result = load_all_plugins(
                registry, app, ["tests.fixtures.plugins.sample_hello"]
            )

        # Verify plugin loaded
        assert result.success_count == 1

        # Verify command was registered
        assert len(registry.registered) == 1
        assert registry.registered[0].__name__ == "HelloCommand"

    def test_sample_plugin_command_execution(self) -> None:
        """Test that the sample plugin command can be executed."""
        from tests.fixtures.plugins.sample_hello import HelloCommand

        # Create minimal app mock
        class MockApp:
            dry_run = False

        app = MockApp()
        cmd = HelloCommand(app)

        # Execute the command
        exit_code = cmd.run(name="Test")
        assert exit_code == 0

    def test_sample_plugin_dry_run(self) -> None:
        """Test sample plugin respects dry-run flag."""
        from tests.fixtures.plugins.sample_hello import HelloCommand

        class MockApp:
            dry_run = True

        app = MockApp()
        cmd = HelloCommand(app)

        exit_code = cmd.run(name="DryRunTest")
        assert exit_code == 0
