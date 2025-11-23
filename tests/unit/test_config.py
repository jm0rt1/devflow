"""Unit tests for configuration loading."""

from devflow.config import load_config
from devflow.config.schema import get_default_config


def test_default_config():
    """Test that default config has expected values."""
    config = get_default_config()

    assert config.venv_dir == ".venv"
    assert config.default_python == "python3"
    assert config.build_backend == "build"
    assert config.test_runner == "pytest"
    assert config.paths.dist_dir == "dist"
    assert config.deps.requirements == "requirements.txt"


def test_load_config_with_pyproject_toml(tmp_path):
    """Test loading config from pyproject.toml."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".custom-venv"
default_python = "python3.11"

[tool.devflow.deps]
requirements = "requirements-custom.txt"
""")

    config = load_config(project_root)

    assert config.venv_dir == ".custom-venv"
    assert config.default_python == "python3.11"
    assert config.deps.requirements == "requirements-custom.txt"
    # Should still have defaults for unspecified values
    assert config.build_backend == "build"


def test_load_config_with_devflow_toml(tmp_path):
    """Test loading config from devflow.toml."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    devflow_toml = project_root / "devflow.toml"
    devflow_toml.write_text("""
venv_dir = ".venv-test"
test_runner = "unittest"
""")

    config = load_config(project_root)

    assert config.venv_dir == ".venv-test"
    assert config.test_runner == "unittest"


def test_load_config_priority_pyproject_over_devflow(tmp_path):
    """Test that pyproject.toml takes priority over devflow.toml."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Create both files
    pyproject = project_root / "pyproject.toml"
    pyproject.write_text("""
[tool.devflow]
venv_dir = ".venv-pyproject"
""")

    devflow_toml = project_root / "devflow.toml"
    devflow_toml.write_text("""
venv_dir = ".venv-devflow"
""")

    config = load_config(project_root)

    # Should use pyproject.toml value
    assert config.venv_dir == ".venv-pyproject"


def test_load_config_explicit_path(tmp_path):
    """Test loading config from explicit path."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    custom_config = tmp_path / "custom-config.toml"
    custom_config.write_text("""
venv_dir = ".venv-custom"
""")

    config = load_config(project_root, config_path=custom_config)

    assert config.venv_dir == ".venv-custom"


def test_load_config_no_config_uses_defaults(tmp_path):
    """Test that default config is used when no config files exist."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    config = load_config(project_root)

    # Should match defaults
    default = get_default_config()
    assert config.venv_dir == default.venv_dir
    assert config.default_python == default.default_python
