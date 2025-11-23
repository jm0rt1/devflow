"""Configuration schema for devflow using Pydantic."""

from typing import Any

from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    """Configuration for project paths."""

    dist_dir: str = "dist"
    tests_dir: str = "tests"
    src_dir: str = "src"


class PublishConfig(BaseModel):
    """Configuration for publishing packages."""

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = False
    tag_format: str = "v{version}"
    tag_prefix: str = ""
    require_clean_working_tree: bool = True


class DepsConfig(BaseModel):
    """Configuration for dependency management."""

    requirements: str = "requirements.txt"
    dev_requirements: str = "requirements-dev.txt"
    freeze_output: str = "requirements-freeze.txt"


class TaskConfig(BaseModel):
    """Configuration for a single task."""

    command: str | None = None
    args: list[str] = Field(default_factory=list)
    use_venv: bool = True
    env: dict[str, str] = Field(default_factory=dict)
    pipeline: list[str] | None = None
    steps: list[str] | None = None


class DevflowConfig(BaseModel):
    """Root configuration for devflow."""

    venv_dir: str = ".venv"
    default_python: str = "python3"
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"
    auto_discover_tasks: bool = False

    paths: PathsConfig = Field(default_factory=PathsConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    deps: DepsConfig = Field(default_factory=DepsConfig)
    tasks: dict[str, TaskConfig] = Field(default_factory=dict)

    @classmethod
    def get_defaults(cls) -> "DevflowConfig":
        """Get default configuration."""
        return cls()

    def merge_with(self, other: dict[str, Any]) -> "DevflowConfig":
        """Merge this config with another dictionary of settings."""
        # Convert current config to dict
        current = self.model_dump()

        # Deep merge logic
        def deep_merge(base: dict, override: dict) -> dict:
            result = base.copy()
            for key, value in override.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(current, other)
        return DevflowConfig.model_validate(merged)
