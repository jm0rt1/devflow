"""Unit tests for configuration loading."""

import tempfile
from pathlib import Path

import pytest

from devflow.config.loader import load_config
from devflow.config.schema import DevflowConfig


class TestConfigLoader:
    """Test configuration loading from different sources."""

    def test_default_config(self):
        """Test loading default configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            # Create empty pyproject.toml
            (project_root / "pyproject.toml").write_text("[project]\nname='test'\n")
            
            config = load_config(project_root)
            
            assert config.venv_dir == ".venv"
            assert config.default_python == "python3"
            assert config.test_runner == "pytest"
            assert config.build_backend == "build"

    def test_pyproject_toml_config(self):
        """Test loading from pyproject.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("""
[tool.devflow]
venv_dir = ".myenv"
default_python = "python3.11"
test_runner = "unittest"

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]
""")
            
            config = load_config(project_root)
            
            assert config.venv_dir == ".myenv"
            assert config.default_python == "python3.11"
            assert config.test_runner == "unittest"
            assert "lint" in config.tasks
            assert config.tasks["lint"].command == "ruff"

    def test_devflow_toml_config(self):
        """Test loading from devflow.toml."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "devflow.toml").write_text("""
[devflow]
venv_dir = ".venv2"
test_runner = "pytest"

[devflow.tasks.test]
command = "pytest"
args = ["-v"]
""")
            
            config = load_config(project_root)
            
            assert config.venv_dir == ".venv2"
            assert config.test_runner == "pytest"
            assert "test" in config.tasks

    def test_pipeline_task(self):
        """Test loading pipeline task configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("""
[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test", "build"]
""")
            
            config = load_config(project_root)
            
            assert "ci-check" in config.tasks
            task = config.tasks["ci-check"]
            assert task.pipeline == ["lint", "test", "build"]

    def test_steps_alias_for_pipeline(self):
        """Test that 'steps' is aliased to 'pipeline'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("""
[tool.devflow.tasks.publish]
steps = ["build", "upload"]
""")
            
            config = load_config(project_root)
            
            assert "publish" in config.tasks
            task = config.tasks["publish"]
            assert task.pipeline == ["build", "upload"]

    def test_list_tasks(self):
        """Test listing configured tasks."""
        with tempfile.TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            (project_root / "pyproject.toml").write_text("""
[tool.devflow.tasks.lint]
command = "ruff"

[tool.devflow.tasks.test]
command = "pytest"

[tool.devflow.tasks.build]
command = "python"
args = ["-m", "build"]
""")
            
            config = load_config(project_root)
            tasks = config.list_tasks()
            
            assert tasks == ["build", "lint", "test"]  # Sorted
