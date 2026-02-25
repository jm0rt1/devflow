"""Tests for configuration loading and schema."""

from pathlib import Path

import pytest

from devflow.config import (
    DEFAULT_CONFIG,
    DevflowConfig,
    TaskConfig,
    find_config_file,
    load_config,
)


class TestDevflowConfigSchema:
    """Tests for DevflowConfig schema and defaults."""

    def test_default_values(self) -> None:
        """Should have sensible default values."""
        config = DevflowConfig()

        assert config.venv_dir == ".venv"
        assert config.default_python == "python3"
        assert config.build_backend == "build"
        assert config.test_runner == "pytest"
        assert config.package_index == "pypi"
        assert config.auto_discover_tasks is True

    def test_nested_defaults(self) -> None:
        """Should have sensible defaults for nested configs."""
        config = DevflowConfig()

        # Paths
        assert config.paths.dist_dir == "dist"
        assert config.paths.tests_dir == "tests"
        assert config.paths.src_dir == "src"

        # Publish
        assert config.publish.repository == "pypi"
        assert config.publish.sign is False
        assert config.publish.tag_on_publish is True
        assert config.publish.tag_format == "v{version}"
        assert config.publish.require_clean_working_tree is True

        # Deps
        assert config.deps.requirements == "requirements.txt"
        assert config.deps.dev_requirements == "requirements-dev.txt"
        assert config.deps.freeze_output == "requirements-freeze.txt"

    def test_from_dict_basic(self) -> None:
        """Should create config from dictionary."""
        data = {
            "venv_dir": ".env",
            "default_python": "python3.11",
        }
        config = DevflowConfig.from_dict(data)

        assert config.venv_dir == ".env"
        assert config.default_python == "python3.11"
        # Other values should be defaults
        assert config.build_backend == "build"

    def test_from_dict_nested(self) -> None:
        """Should handle nested configuration dictionaries."""
        data = {
            "paths": {
                "dist_dir": "output",
                "src_dir": "lib",
            },
            "publish": {
                "sign": True,
                "tag_format": "release-{version}",
            },
        }
        config = DevflowConfig.from_dict(data)

        assert config.paths.dist_dir == "output"
        assert config.paths.src_dir == "lib"
        assert config.paths.tests_dir == "tests"  # default preserved

        assert config.publish.sign is True
        assert config.publish.tag_format == "release-{version}"
        assert config.publish.repository == "pypi"  # default preserved

    def test_from_dict_with_tasks(self) -> None:
        """Should parse task configurations."""
        data = {
            "tasks": {
                "test": {
                    "command": "pytest",
                    "args": ["-q", "--tb=short"],
                    "use_venv": True,
                },
                "lint": {
                    "command": "ruff",
                    "args": ["check", "."],
                },
                "ci": {
                    "pipeline": ["lint", "test"],
                },
            },
        }
        config = DevflowConfig.from_dict(data)

        assert "test" in config.tasks
        assert "lint" in config.tasks
        assert "ci" in config.tasks

        assert config.tasks["test"].command == "pytest"
        assert config.tasks["test"].args == ["-q", "--tb=short"]
        assert config.tasks["test"].use_venv is True

        assert config.tasks["ci"].pipeline == ["lint", "test"]


class TestConfigMerging:
    """Tests for configuration merging behavior."""

    def test_merge_overwrites_scalar(self) -> None:
        """Merged values should override base values."""
        base = DevflowConfig()
        overrides = {"venv_dir": ".custom-venv", "test_runner": "unittest"}

        merged = base.merge_with(overrides)

        assert merged.venv_dir == ".custom-venv"
        assert merged.test_runner == "unittest"
        # Unspecified values preserved
        assert merged.default_python == "python3"

    def test_merge_deep_nested(self) -> None:
        """Should deep merge nested dictionaries."""
        base = DevflowConfig()
        overrides = {
            "paths": {"dist_dir": "build"},
            "publish": {"sign": True},
        }

        merged = base.merge_with(overrides)

        assert merged.paths.dist_dir == "build"
        assert merged.paths.tests_dir == "tests"  # preserved from base
        assert merged.publish.sign is True
        assert merged.publish.repository == "pypi"  # preserved from base

    def test_merge_does_not_modify_original(self) -> None:
        """Merging should not modify the original config."""
        base = DevflowConfig()
        original_venv = base.venv_dir

        merged = base.merge_with({"venv_dir": "different"})

        assert base.venv_dir == original_venv
        assert merged.venv_dir == "different"

    def test_project_overrides_take_precedence(self) -> None:
        """Project-level overrides should take precedence over defaults."""
        # This simulates the config loading behavior
        defaults = DEFAULT_CONFIG
        project_config = {
            "test_runner": "unittest",
            "paths": {"src_dir": "library"},
        }

        final = defaults.merge_with(project_config)

        assert final.test_runner == "unittest"
        assert final.paths.src_dir == "library"
        # Defaults for unspecified values
        assert final.venv_dir == ".venv"
        assert final.paths.dist_dir == "dist"


class TestConfigLoading:
    """Tests for configuration file loading."""

    def test_load_from_pyproject_toml(self, tmp_path: Path) -> None:
        """Should load config from [tool.devflow] in pyproject.toml."""
        pyproject_content = """
[project]
name = "test-project"
version = "0.1.0"

[tool.devflow]
venv_dir = ".project-venv"
default_python = "python3.11"
test_runner = "pytest"

[tool.devflow.paths]
src_dir = "src"
dist_dir = "dist"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)

        config = load_config(tmp_path)

        assert config.venv_dir == ".project-venv"
        assert config.default_python == "python3.11"
        assert config.paths.src_dir == "src"

    def test_load_from_devflow_toml(self, tmp_path: Path) -> None:
        """Should load config from devflow.toml."""
        devflow_content = """
[devflow]
venv_dir = ".devflow-venv"
build_backend = "hatchling"

[devflow.publish]
repository = "testpypi"
"""
        (tmp_path / "devflow.toml").write_text(devflow_content)

        config = load_config(tmp_path)

        assert config.venv_dir == ".devflow-venv"
        assert config.build_backend == "hatchling"
        assert config.publish.repository == "testpypi"

    def test_load_flat_devflow_toml(self, tmp_path: Path) -> None:
        """Should load flat devflow.toml without [devflow] section."""
        devflow_content = """
venv_dir = ".flat-venv"
test_runner = "nose2"
"""
        (tmp_path / "devflow.toml").write_text(devflow_content)

        config = load_config(tmp_path)

        assert config.venv_dir == ".flat-venv"
        assert config.test_runner == "nose2"

    def test_pyproject_takes_precedence_over_devflow(self, tmp_path: Path) -> None:
        """pyproject.toml should take precedence over devflow.toml."""
        pyproject_content = """
[tool.devflow]
venv_dir = ".pyproject-venv"
"""
        devflow_content = """
[devflow]
venv_dir = ".devflow-venv"
"""
        (tmp_path / "pyproject.toml").write_text(pyproject_content)
        (tmp_path / "devflow.toml").write_text(devflow_content)

        config = load_config(tmp_path)

        assert config.venv_dir == ".pyproject-venv"

    def test_explicit_config_path(self, tmp_path: Path) -> None:
        """Should use explicit config path when provided."""
        custom_config = """
[devflow]
venv_dir = ".custom-venv"
"""
        custom_path = tmp_path / "custom" / "config.toml"
        custom_path.parent.mkdir(parents=True)
        custom_path.write_text(custom_config)

        # Also create pyproject.toml that should be ignored
        (tmp_path / "pyproject.toml").write_text("""
[tool.devflow]
venv_dir = ".pyproject-venv"
""")

        config = load_config(tmp_path, explicit_config=custom_path)

        assert config.venv_dir == ".custom-venv"

    def test_explicit_config_not_found(self, tmp_path: Path) -> None:
        """Should raise error when explicit config doesn't exist."""
        nonexistent = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_config(tmp_path, explicit_config=nonexistent)

        assert "not found" in str(exc_info.value)

    def test_returns_defaults_when_no_config(self, tmp_path: Path) -> None:
        """Should return defaults when no config files exist."""
        # Create a pyproject.toml without [tool.devflow]
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")

        config = load_config(tmp_path)

        assert config.venv_dir == DEFAULT_CONFIG.venv_dir
        assert config.default_python == DEFAULT_CONFIG.default_python


class TestFindConfigFile:
    """Tests for config file discovery."""

    def test_find_explicit_config(self, tmp_path: Path) -> None:
        """Should return explicit config path when provided."""
        config_path = tmp_path / "my-config.toml"
        config_path.write_text("[devflow]\n")

        result = find_config_file(tmp_path, explicit_config=config_path)

        assert result == config_path

    def test_find_pyproject_with_devflow(self, tmp_path: Path) -> None:
        """Should find pyproject.toml with [tool.devflow] section."""
        (tmp_path / "pyproject.toml").write_text("[tool.devflow]\nvenv_dir = '.venv'\n")

        result = find_config_file(tmp_path)

        assert result == tmp_path / "pyproject.toml"

    def test_skip_pyproject_without_devflow(self, tmp_path: Path) -> None:
        """Should skip pyproject.toml without [tool.devflow] section."""
        (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n")
        (tmp_path / "devflow.toml").write_text("[devflow]\n")

        result = find_config_file(tmp_path)

        assert result == tmp_path / "devflow.toml"

    def test_find_devflow_toml(self, tmp_path: Path) -> None:
        """Should find devflow.toml when pyproject.toml has no devflow config."""
        (tmp_path / "devflow.toml").write_text("[devflow]\n")

        result = find_config_file(tmp_path)

        assert result == tmp_path / "devflow.toml"

    def test_returns_none_when_no_config(self, tmp_path: Path) -> None:
        """Should return None when no config files exist."""
        result = find_config_file(tmp_path)

        assert result is None

    def test_explicit_config_not_found_raises(self, tmp_path: Path) -> None:
        """Should raise when explicit config path doesn't exist."""
        nonexistent = tmp_path / "nonexistent.toml"

        with pytest.raises(FileNotFoundError):
            find_config_file(tmp_path, explicit_config=nonexistent)


class TestTaskConfig:
    """Tests for task configuration."""

    def test_task_defaults(self) -> None:
        """Task should have sensible defaults."""
        task = TaskConfig()

        assert task.command is None
        assert task.args == []
        assert task.use_venv is True
        assert task.env == {}
        assert task.pipeline is None
        assert task.steps is None

    def test_task_with_command(self) -> None:
        """Should accept command and args."""
        task = TaskConfig(command="pytest", args=["-v", "--tb=short"])

        assert task.command == "pytest"
        assert task.args == ["-v", "--tb=short"]

    def test_pipeline_task(self) -> None:
        """Should accept pipeline definition."""
        task = TaskConfig(pipeline=["lint", "test", "build"])

        assert task.pipeline == ["lint", "test", "build"]
        assert task.command is None
