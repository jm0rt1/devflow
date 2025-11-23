"""Tests for configuration loading."""


import pytest

from devflow.config import AppConfig, TaskConfig, load_config


def test_default_config():
    """Test that default config has expected values."""
    config = AppConfig()

    assert config.venv_dir == ".venv"
    assert config.default_python == "python3"
    assert config.build_backend == "build"
    assert config.test_runner == "pytest"


def test_config_from_dict():
    """Test creating config from dictionary."""
    data = {
        "venv_dir": ".env",
        "default_python": "python3.11",
        "tasks": {
            "test": {
                "command": "pytest",
                "args": ["-v"],
            }
        }
    }

    config = AppConfig.from_dict(data)

    assert config.venv_dir == ".env"
    assert config.default_python == "python3.11"
    assert "test" in config.tasks
    assert config.tasks["test"].command == "pytest"
    assert config.tasks["test"].args == ["-v"]


def test_task_config_command():
    """Test command-based task config."""
    task = TaskConfig(command="pytest", args=["-v"])

    assert task.is_command() is True
    assert task.is_pipeline() is False


def test_task_config_pipeline():
    """Test pipeline-based task config."""
    task = TaskConfig(pipeline=["lint", "test"])

    assert task.is_command() is False
    assert task.is_pipeline() is True


def test_load_config_from_pyproject_toml(tmp_path):
    """Test loading config from pyproject.toml."""
    project = tmp_path / "project"
    project.mkdir()

    pyproject = project / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv"
default_python = "python3.11"

[tool.devflow.tasks.test]
command = "pytest"
args = ["-v"]
""")

    config = load_config(project)

    assert config.venv_dir == ".venv"
    assert config.default_python == "python3.11"
    assert "test" in config.tasks


def test_load_config_from_devflow_toml(tmp_path):
    """Test loading config from devflow.toml."""
    project = tmp_path / "project"
    project.mkdir()

    devflow_toml = project / "devflow.toml"
    devflow_toml.write_text("""
[devflow]
venv_dir = ".venv-custom"

[devflow.tasks.lint]
command = "ruff"
args = ["check"]
""")

    config = load_config(project)

    assert config.venv_dir == ".venv-custom"
    assert "lint" in config.tasks


def test_load_config_explicit_path(tmp_path):
    """Test loading config from explicit path."""
    project = tmp_path / "project"
    project.mkdir()

    custom_config = tmp_path / "custom.toml"
    custom_config.write_text("""
[devflow]
venv_dir = ".custom-venv"
""")

    config = load_config(project, config_path=custom_config)

    assert config.venv_dir == ".custom-venv"


def test_load_config_no_file_uses_defaults(tmp_path):
    """Test that missing config file uses defaults."""
    project = tmp_path / "project"
    project.mkdir()

    config = load_config(project)

    # Should have default values
    assert config.venv_dir == ".venv"
    assert config.default_python == "python3"


def test_load_config_explicit_path_not_found(tmp_path):
    """Test error when explicit config path doesn't exist."""
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(FileNotFoundError):
        load_config(project, config_path=project / "nonexistent.toml")
