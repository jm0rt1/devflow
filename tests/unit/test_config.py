"""Tests for configuration loading and merging."""

import tempfile
from pathlib import Path

from devflow.config import DevflowConfig, load_config


def test_default_config():
    """Test default configuration values."""
    config = DevflowConfig.get_defaults()

    assert config.venv_dir == ".venv"
    assert config.default_python == "python3"
    assert config.build_backend == "build"
    assert config.test_runner == "pytest"
    assert config.package_index == "pypi"
    assert config.paths.dist_dir == "dist"
    assert config.paths.tests_dir == "tests"
    assert config.paths.src_dir == "src"
    assert config.publish.repository == "pypi"
    assert config.publish.sign is False
    assert config.deps.requirements == "requirements.txt"


def test_config_merge():
    """Test merging configurations."""
    base = DevflowConfig.get_defaults()

    # Merge with some overrides
    override = {
        "venv_dir": ".virtualenv",
        "default_python": "python3.11",
        "paths": {"dist_dir": "build"},
    }

    merged = base.merge_with(override)

    # Check overridden values
    assert merged.venv_dir == ".virtualenv"
    assert merged.default_python == "python3.11"
    assert merged.paths.dist_dir == "build"

    # Check that non-overridden values are preserved
    assert merged.build_backend == "build"
    assert merged.paths.tests_dir == "tests"
    assert merged.paths.src_dir == "src"


def test_load_config_from_pyproject_toml():
    """Test loading config from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create pyproject.toml with devflow config
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow]
venv_dir = ".my-venv"
default_python = "python3.10"
build_backend = "hatchling"

[tool.devflow.paths]
dist_dir = "artifacts"

[tool.devflow.publish]
repository = "testpypi"
sign = true
"""
        )

        config = load_config(project_root=root)

        assert config.venv_dir == ".my-venv"
        assert config.default_python == "python3.10"
        assert config.build_backend == "hatchling"
        assert config.paths.dist_dir == "artifacts"
        assert config.publish.repository == "testpypi"
        assert config.publish.sign is True

        # Check defaults are still present
        assert config.test_runner == "pytest"
        assert config.paths.tests_dir == "tests"


def test_load_config_from_devflow_toml():
    """Test loading config from devflow.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create devflow.toml
        devflow_toml = root / "devflow.toml"
        devflow_toml.write_text(
            """
[devflow]
venv_dir = ".env"
test_runner = "unittest"

[devflow.deps]
requirements = "reqs.txt"
"""
        )

        config = load_config(project_root=root)

        assert config.venv_dir == ".env"
        assert config.test_runner == "unittest"
        assert config.deps.requirements == "reqs.txt"

        # Check defaults are still present
        assert config.default_python == "python3"
        assert config.build_backend == "build"


def test_load_config_pyproject_takes_precedence():
    """Test that pyproject.toml takes precedence over devflow.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create both files
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow]
venv_dir = ".venv-pyproject"
"""
        )

        devflow_toml = root / "devflow.toml"
        devflow_toml.write_text(
            """
[devflow]
venv_dir = ".venv-devflow"
"""
        )

        config = load_config(project_root=root)

        # pyproject.toml should win
        assert config.venv_dir == ".venv-pyproject"


def test_load_config_with_explicit_path():
    """Test loading config from explicit path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create custom config file
        custom_config = root / "custom.toml"
        custom_config.write_text(
            """
[tool.devflow]
venv_dir = ".custom-venv"
default_python = "python3.12"
"""
        )

        # Also create pyproject.toml that should be ignored
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow]
venv_dir = ".ignored-venv"
"""
        )

        config = load_config(config_path=custom_config, project_root=root)

        # Should use custom config, not pyproject
        assert config.venv_dir == ".custom-venv"
        assert config.default_python == "python3.12"


def test_load_config_no_project_root_uses_defaults():
    """Test that load_config uses defaults when no project root found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        # Don't create any config files

        config = load_config(project_root=root)

        # Should get all defaults
        assert config.venv_dir == ".venv"
        assert config.default_python == "python3"
        assert config.build_backend == "build"


def test_config_with_tasks():
    """Test loading config with task definitions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow.tasks.test]
command = "pytest"
args = ["-v", "--cov"]
use_venv = true

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]

[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test"]
"""
        )

        config = load_config(project_root=root)

        assert "test" in config.tasks
        assert config.tasks["test"].command == "pytest"
        assert config.tasks["test"].args == ["-v", "--cov"]
        assert config.tasks["test"].use_venv is True

        assert "lint" in config.tasks
        assert config.tasks["lint"].command == "ruff"
        assert config.tasks["lint"].args == ["check", "."]

        assert "ci-check" in config.tasks
        assert config.tasks["ci-check"].pipeline == ["lint", "test"]
