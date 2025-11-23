"""Configuration schema for devflow using Pydantic."""

from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PathsConfig(BaseModel):
    """Configuration for project paths."""

    dist_dir: str = "dist"
    tests_dir: str = "tests"
    src_dir: str = "src"


class PublishConfig(BaseModel):
    """Configuration for publishing."""

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = False
    tag_format: str = "v{version}"
    require_clean_working_tree: bool = True


class DepsConfig(BaseModel):
    """Configuration for dependency management."""

    requirements: str = "requirements.txt"
    dev_requirements: Optional[str] = None
    freeze_output: str = "requirements-freeze.txt"


class TaskConfig(BaseModel):
    """Configuration for a single task."""

    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    use_venv: bool = True
    env: Dict[str, str] = Field(default_factory=dict)
    pipeline: Optional[List[str]] = None
    steps: Optional[List[str]] = None  # Alias for pipeline


class DevflowConfig(BaseModel):
    """Main configuration for devflow."""

    # Environment
    venv_dir: str = ".venv"
    default_python: str = "python3"

    # Build and test
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"

    # Subsection configs
    paths: PathsConfig = Field(default_factory=PathsConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    deps: DepsConfig = Field(default_factory=DepsConfig)

    # Tasks
    tasks: Dict[str, TaskConfig] = Field(default_factory=dict)

    # Auto-discovery
    auto_discover_tasks: bool = True

    model_config = ConfigDict(extra="allow")  # Allow additional fields for extensibility


def get_default_config() -> DevflowConfig:
    """Get the default configuration."""
    return DevflowConfig()
