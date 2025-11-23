"""Configuration schema definitions."""

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
    """Configuration for publishing."""

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = False
    tag_format: str = "v{version}"
    require_clean_working_tree: bool = True


@dataclass
class DepsConfig:
    """Configuration for dependency management."""

    requirements: str = "requirements.txt"
    dev_requirements: str | None = None
    freeze_output: str = "requirements-freeze.txt"


@dataclass
class TaskConfig:
    """Configuration for a single task."""

    command: str | None = None
    args: list[str] = field(default_factory=list)
    use_venv: bool = True
    env: dict[str, str] = field(default_factory=dict)
    pipeline: list[str] | None = None  # For composite tasks

    def is_pipeline(self) -> bool:
        """Check if this is a pipeline task."""
        return self.pipeline is not None

    def is_command(self) -> bool:
        """Check if this is a command task."""
        return self.command is not None


@dataclass
class AppConfig:
    """Main application configuration."""

    venv_dir: str = ".venv"
    default_python: str = "python3"
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"
    auto_discover_tasks: bool = True

    paths: PathsConfig = field(default_factory=PathsConfig)
    publish: PublishConfig = field(default_factory=PublishConfig)
    deps: DepsConfig = field(default_factory=DepsConfig)
    tasks: dict[str, TaskConfig] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AppConfig":
        """Create config from dictionary."""
        # Extract nested configs
        paths_data = data.pop("paths", {})
        publish_data = data.pop("publish", {})
        deps_data = data.pop("deps", {})
        tasks_data = data.pop("tasks", {})

        # Build nested configs
        paths = PathsConfig(**paths_data)
        publish = PublishConfig(**publish_data)
        deps = DepsConfig(**deps_data)

        # Build task configs
        tasks = {}
        for name, task_data in tasks_data.items():
            # Handle both dict and already-parsed TaskConfig
            if isinstance(task_data, TaskConfig):
                tasks[name] = task_data
            else:
                tasks[name] = TaskConfig(**task_data)

        return cls(
            paths=paths,
            publish=publish,
            deps=deps,
            tasks=tasks,
            **data
        )

    def merge_with_defaults(self, defaults: "AppConfig") -> "AppConfig":
        """Merge this config with defaults, preferring this config's values."""
        # This is a simplified merge - a full implementation would recursively merge
        return self
