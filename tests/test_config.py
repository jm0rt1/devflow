"""Tests for configuration loading."""

import tempfile
from pathlib import Path


from devflow.config.loader import load_config


class TestConfigLoader:
    """Tests for config file loading."""
    
    def test_load_empty_config(self):
        """Test loading when no config files exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            config = load_config(project_root)
            assert config == {}
    
    def test_load_from_pyproject_toml(self):
        """Test loading from [tool.devflow] in pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            pyproject = project_root / "pyproject.toml"
            pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
default_python = "python3.11"

[tool.devflow.plugins]
modules = ["my.plugin"]
""")
            
            config = load_config(project_root)
            assert config['venv_dir'] == ".venv"
            assert config['default_python'] == "python3.11"
            assert config['plugins']['modules'] == ["my.plugin"]
    
    def test_load_from_devflow_toml(self):
        """Test loading from devflow.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            devflow_toml = project_root / "devflow.toml"
            devflow_toml.write_text("""
venv_dir = ".venv"

[plugins]
modules = ["another.plugin"]
""")
            
            config = load_config(project_root)
            assert config['plugins']['modules'] == ["another.plugin"]
            assert config['venv_dir'] == ".venv"
    
    def test_load_from_explicit_path(self):
        """Test loading from explicit config path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            custom_config = project_root / "custom.toml"
            custom_config.write_text("""
[tool.devflow]
venv_dir = ".custom_venv"
""")
            
            config = load_config(project_root, custom_config)
            assert config['venv_dir'] == ".custom_venv"
    
    def test_pyproject_takes_precedence_over_devflow_toml(self):
        """Test that pyproject.toml takes precedence over devflow.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create both files
            pyproject = project_root / "pyproject.toml"
            pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv_from_pyproject"
""")
            
            devflow_toml = project_root / "devflow.toml"
            devflow_toml.write_text("""
venv_dir = ".venv_from_devflow_toml"
""")
            
            config = load_config(project_root)
            # pyproject.toml should take precedence
            assert config['venv_dir'] == ".venv_from_pyproject"
    
    def test_load_root_level_devflow_toml(self):
        """Test loading from root-level config in devflow.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            devflow_toml = project_root / "devflow.toml"
            devflow_toml.write_text("""
venv_dir = ".venv"
test_runner = "pytest"
""")
            
            config = load_config(project_root)
            assert config['venv_dir'] == ".venv"
            assert config['test_runner'] == "pytest"
