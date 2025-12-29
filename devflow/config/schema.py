"""Typed configuration schema for devflow.

This module defines dataclass models that represent the devflow configuration.
The schema mirrors the sample TOML from the design specification.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PathsConfig:
    """Configuration for project paths."""

    dist_dir: str = "dist"
    tests_dir: str = "tests"
    src_dir: str = "src"


@dataclass
class PublishConfig:
    """Configuration for publish operations."""

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = True
    tag_format: str = "v{version}"
    tag_prefix: str = ""
    require_clean_working_tree: bool = True


@dataclass
class DepsConfig:
    """Configuration for dependency management."""

    requirements: str = "requirements.txt"
    dev_requirements: str = "requirements-dev.txt"
    freeze_output: str = "requirements-freeze.txt"


@dataclass
class TaskConfig:
    """Configuration for a single task or pipeline."""

    command: str | None = None
    args: list[str] = field(default_factory=list)
    use_venv: bool = True
    env: dict[str, str] = field(default_factory=dict)
    # For pipelines/composite tasks
    pipeline: list[str] | None = None
    steps: list[str] | None = None


@dataclass
class DevflowConfig:
    """Main configuration schema for devflow.

    This encapsulates all configuration options available in [tool.devflow].
    """

    # Core settings
    venv_dir: str = ".venv"
    default_python: str = "python3"
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"

    # Boolean flags
    auto_discover_tasks: bool = True

    # Nested configurations
    paths: PathsConfig = field(default_factory=PathsConfig)
    publish: PublishConfig = field(default_factory=PublishConfig)
    deps: DepsConfig = field(default_factory=DepsConfig)

    # Tasks dictionary - maps task names to TaskConfig
    tasks: dict[str, TaskConfig] = field(default_factory=dict)

    # Version source for git integration (placeholder for Workstream E)
    version_source: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DevflowConfig:
        """Create a DevflowConfig from a dictionary.

        Handles nested configuration objects and provides defaults for missing values.
        """
        # Make a copy to avoid modifying the input
        data = dict(data)

        # Extract nested configs without modifying original
        paths_data = data.pop("paths", {})
        publish_data = data.pop("publish", {})
        deps_data = data.pop("deps", {})
        tasks_data = data.pop("tasks", {})

        # Build nested config objects
        paths = PathsConfig(**paths_data) if paths_data else PathsConfig()
        publish = PublishConfig(**publish_data) if publish_data else PublishConfig()
        deps = DepsConfig(**deps_data) if deps_data else DepsConfig()

        # Build tasks dictionary
        tasks: dict[str, TaskConfig] = {}
        for task_name, task_config in tasks_data.items():
            if isinstance(task_config, dict):
                tasks[task_name] = TaskConfig(**task_config)
            else:
                tasks[task_name] = TaskConfig()

        return cls(
            paths=paths,
            publish=publish,
            deps=deps,
            tasks=tasks,
            **data,
        )

    def merge_with(self, overrides: dict[str, Any]) -> DevflowConfig:
        """Merge this config with overrides, returning a new config.

        Overrides take precedence over existing values.
        """
        # Start with current config as a dict
        current = {
            "venv_dir": self.venv_dir,
            "default_python": self.default_python,
            "build_backend": self.build_backend,
            "test_runner": self.test_runner,
            "package_index": self.package_index,
            "auto_discover_tasks": self.auto_discover_tasks,
            "version_source": self.version_source,
            "paths": {
                "dist_dir": self.paths.dist_dir,
                "tests_dir": self.paths.tests_dir,
                "src_dir": self.paths.src_dir,
            },
            "publish": {
                "repository": self.publish.repository,
                "sign": self.publish.sign,
                "tag_on_publish": self.publish.tag_on_publish,
                "tag_format": self.publish.tag_format,
                "tag_prefix": self.publish.tag_prefix,
                "require_clean_working_tree": self.publish.require_clean_working_tree,
            },
            "deps": {
                "requirements": self.deps.requirements,
                "dev_requirements": self.deps.dev_requirements,
                "freeze_output": self.deps.freeze_output,
            },
            "tasks": {
                name: {
                    "command": task.command,
                    "args": task.args,
                    "use_venv": task.use_venv,
                    "env": task.env,
                    "pipeline": task.pipeline,
                    "steps": task.steps,
                }
                for name, task in self.tasks.items()
            },
        }

        # Deep merge overrides
        _deep_merge(current, overrides)

        return DevflowConfig.from_dict(current)


def _deep_merge(base: dict[str, Any], overrides: dict[str, Any]) -> None:
    """Recursively merge overrides into base dict (in place)."""
    for key, value in overrides.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
