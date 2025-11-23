"""Configuration schema for devflow."""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    """Path configuration."""

    dist_dir: str = "dist"
    tests_dir: str = "tests"
    src_dir: str = "src"


class PublishConfig(BaseModel):
    """Publish configuration."""

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = False
    tag_format: str = "v{version}"
    require_clean_working_tree: bool = True
    run_tests_before_publish: bool = True
    skip_existing: bool = False


class DepsConfig(BaseModel):
    """Dependencies configuration."""

    requirements: str = "requirements.txt"
    dev_requirements: Optional[str] = "requirements-dev.txt"
    freeze_output: str = "requirements-freeze.txt"


class TaskConfig(BaseModel):
    """Single task configuration."""

    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    use_venv: bool = True
    env: Dict[str, str] = Field(default_factory=dict)
    pipeline: Optional[List[str]] = None


class DevFlowConfig(BaseModel):
    """Main devflow configuration."""

    model_config = {"extra": "allow"}

    venv_dir: str = ".venv"
    default_python: str = "python3"
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"
    auto_discover_tasks: bool = True

    paths: PathsConfig = Field(default_factory=PathsConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    deps: DepsConfig = Field(default_factory=DepsConfig)
    tasks: Dict[str, TaskConfig] = Field(default_factory=dict)
