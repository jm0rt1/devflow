"""Unit tests for configuration loading."""

from pathlib import Path

from devflow.config.loader import load_config
from devflow.config.schema import DevFlowConfig


def test_load_config_defaults(tmp_path: Path):
    """Test loading config with defaults when no config file exists."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()
    (project_dir / "pyproject.toml").write_text("[project]\nname = 'test'\n")

    config = load_config(project_dir)

    assert config.venv_dir == ".venv"
    assert config.test_runner == "pytest"
    assert config.build_backend == "build"


def test_load_config_from_pyproject(tmp_path: Path):
    """Test loading config from pyproject.toml."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    pyproject_content = """
[project]
name = "test"

[tool.devflow]
venv_dir = ".custom_venv"
test_runner = "unittest"
build_backend = "hatchling"
"""
    (project_dir / "pyproject.toml").write_text(pyproject_content)

    config = load_config(project_dir)

    assert config.venv_dir == ".custom_venv"
    assert config.test_runner == "unittest"
    assert config.build_backend == "hatchling"


def test_load_config_from_devflow_toml(tmp_path: Path):
    """Test loading config from devflow.toml."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    devflow_content = """
[devflow]
venv_dir = ".venv2"
test_runner = "tox"
"""
    (project_dir / "devflow.toml").write_text(devflow_content)

    config = load_config(project_dir)

    assert config.venv_dir == ".venv2"
    assert config.test_runner == "tox"


def test_load_config_explicit_path(tmp_path: Path):
    """Test loading config from explicit path."""
    project_dir = tmp_path / "project"
    project_dir.mkdir()

    config_path = project_dir / "custom_config.toml"
    config_content = """
[devflow]
venv_dir = ".custom"
"""
    config_path.write_text(config_content)

    config = load_config(project_dir, config_path=config_path)

    assert config.venv_dir == ".custom"


def test_config_schema_validation():
    """Test that config schema validates correctly."""
    config = DevFlowConfig(
        venv_dir=".venv",
        test_runner="pytest",
    )

    assert config.venv_dir == ".venv"
    assert config.test_runner == "pytest"
    assert config.paths.dist_dir == "dist"  # Default
    assert config.publish.repository == "pypi"  # Default


def test_config_nested_structures():
    """Test that nested config structures work."""
    config = DevFlowConfig(
        paths={"dist_dir": "build/dist"},
        publish={
            "repository": "testpypi",
            "tag_on_publish": True,
        },
    )

    assert config.paths.dist_dir == "build/dist"
    assert config.publish.repository == "testpypi"
    assert config.publish.tag_on_publish is True
