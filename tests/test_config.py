"""Tests for configuration schema."""

import pytest
from pydantic import ValidationError

from devflow.config.schema import DevflowConfig, PublishConfig


class TestPublishConfig:
    """Tests for PublishConfig schema."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = PublishConfig()
        assert config.repository == "pypi"
        assert config.sign is False
        assert config.tag_on_publish is True
        assert config.tag_format == "v{version}"
        assert config.tag_prefix == ""
        assert config.require_clean_working_tree is True
        assert config.version_source == "setuptools_scm"

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = PublishConfig(
            repository="testpypi",
            sign=True,
            tag_on_publish=False,
            tag_format="release-{version}",
            tag_prefix="prod/",
            require_clean_working_tree=False,
            version_source="git_tags",
        )
        assert config.repository == "testpypi"
        assert config.sign is True
        assert config.tag_on_publish is False
        assert config.tag_format == "release-{version}"
        assert config.tag_prefix == "prod/"
        assert config.require_clean_working_tree is False
        assert config.version_source == "git_tags"

    def test_version_source_validation(self) -> None:
        """Test that version_source only accepts valid values."""
        # Valid values
        for source in ["setuptools_scm", "config", "pyproject"]:
            config = PublishConfig(version_source=source)
            assert config.version_source == source

        # Invalid value should raise ValidationError
        with pytest.raises(ValidationError):
            PublishConfig(version_source="invalid")


class TestDevflowConfig:
    """Tests for DevflowConfig schema."""

    def test_default_values(self) -> None:
        """Test that default values are set correctly."""
        config = DevflowConfig()
        assert config.venv_dir == ".venv"
        assert config.default_python == "python3"
        assert config.build_backend == "build"
        assert config.test_runner == "pytest"
        assert config.package_index == "pypi"
        assert config.auto_discover_tasks is True

        # Check nested configs
        assert config.paths.dist_dir == "dist"
        assert config.publish.tag_on_publish is True
        assert config.deps.requirements == "requirements.txt"

    def test_custom_values(self) -> None:
        """Test setting custom values."""
        config = DevflowConfig(
            venv_dir="venv",
            default_python="python3.11",
            build_backend="hatchling",
            test_runner="unittest",
        )
        assert config.venv_dir == "venv"
        assert config.default_python == "python3.11"
        assert config.build_backend == "hatchling"
        assert config.test_runner == "unittest"

    def test_nested_config_override(self) -> None:
        """Test overriding nested configuration."""
        config = DevflowConfig(
            publish=PublishConfig(
                tag_format="release-{version}",
                require_clean_working_tree=False,
            )
        )
        assert config.publish.tag_format == "release-{version}"
        assert config.publish.require_clean_working_tree is False
        # Other defaults should still be set
        assert config.publish.repository == "pypi"

    def test_partial_nested_config(self) -> None:
        """Test partial override of nested configuration."""
        config = DevflowConfig.model_validate(
            {
                "venv_dir": ".venv",
                "publish": {
                    "tag_format": "v{version}",
                    "tag_on_publish": False,
                },
            }
        )
        assert config.publish.tag_format == "v{version}"
        assert config.publish.tag_on_publish is False
        # Defaults should still apply
        assert config.publish.require_clean_working_tree is True
