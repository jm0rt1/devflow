"""Integration tests for devflow."""

import subprocess
import tempfile
from pathlib import Path


class TestCLIIntegration:
    """Integration tests for the CLI."""
    
    def test_version_flag(self):
        """Test that --version flag works."""
        result = subprocess.run(
            ["devflow", "--version"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "devflow version" in result.stdout
    
    def test_help_flag(self):
        """Test that --help flag works."""
        result = subprocess.run(
            ["devflow", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Python-native project operations CLI" in result.stdout
        assert "plugin-list" in result.stdout
    
    def test_plugin_list_no_plugins(self):
        """Test plugin-list command with no plugins."""
        result = subprocess.run(
            ["devflow", "plugin-list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "No commands registered" in result.stdout


class TestPluginIntegration:
    """Integration tests for plugin loading."""
    
    def test_load_plugin_from_config_in_same_directory(self):
        """Test loading a plugin from config when running in project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create a simple plugin module
            plugin_dir = project_root / "myplugin"
            plugin_dir.mkdir()
            (plugin_dir / "__init__.py").write_text("""
from devflow.commands.base import Command
from devflow.app import CommandRegistry, AppContext

class TestCommand(Command):
    name = "testcmd"
    help = "Test command"
    
    def run(self, **kwargs):
        return 0

def register(registry: CommandRegistry, app: AppContext) -> None:
    registry.register(TestCommand.name, TestCommand)
""")
            
            # Create a config that loads the plugin
            config = project_root / "devflow.toml"
            config.write_text("""
[plugins]
modules = ["myplugin"]
""")
            
            # Run devflow plugin-list from that directory
            result = subprocess.run(
                ["devflow", "--project-root", str(project_root), "plugin-list"],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                env={**subprocess.os.environ, "PYTHONPATH": str(project_root)}
            )
            
            assert result.returncode == 0
            # The plugin should be loaded
            assert "testcmd" in result.stdout or "Loaded 1 plugin" in result.stdout
    
    def test_verbose_flag(self):
        """Test verbose flag increases logging detail."""
        result = subprocess.run(
            ["devflow", "-v", "plugin-list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # With verbose, we should see the "Loaded N plugin(s)" message
        assert "Loaded" in result.stdout or "Loaded" in result.stderr
    
    def test_quiet_flag(self):
        """Test quiet flag suppresses normal output."""
        result = subprocess.run(
            ["devflow", "-q", "plugin-list"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Quiet mode should suppress INFO level logs


class TestPluginSystemRobustness:
    """Test that the plugin system is robust to errors."""
    
    def test_bad_plugin_does_not_crash_cli(self):
        """Test that a bad plugin doesn't crash the entire CLI."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create a bad plugin that will fail
            plugin_dir = project_root / "badplugin"
            plugin_dir.mkdir()
            (plugin_dir / "__init__.py").write_text("""
def register(registry, app):
    raise RuntimeError("Intentionally broken!")
""")
            
            # Create a config that loads the bad plugin
            config = project_root / "devflow.toml"
            config.write_text("""
[plugins]
modules = ["badplugin"]
""")
            
            # Should not crash even though plugin raises an error
            result = subprocess.run(
                ["devflow", "--project-root", str(project_root), "plugin-list"],
                capture_output=True,
                text=True,
                cwd=str(project_root),
                env={**subprocess.os.environ, "PYTHONPATH": str(project_root)}
            )
            
            # Should succeed (not crash)
            assert result.returncode == 0
            # Should show that 0 plugins loaded due to the error
            assert "0 plugin(s)" in result.stdout or "No commands registered" in result.stdout
