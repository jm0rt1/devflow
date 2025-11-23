"""Configuration schema for devflow."""

from typing import Literal

from pydantic import BaseModel, Field


class PublishConfig(BaseModel):
    """
    Configuration for publish operations.

    Attributes:
        repository: Target package repository (e.g., "pypi", "testpypi"). Default: "pypi"
        sign: Whether to sign packages with GPG before uploading. Default: False
        tag_on_publish: Automatically create a git tag when publishing. Default: True
        tag_format: Format string for git tags with {version} placeholder. Default: "v{version}"
        tag_prefix: Additional prefix to prepend to formatted tag. Default: ""
        require_clean_working_tree: Require no uncommitted changes before publishing. Default: True
        version_source: Source for version information. Valid values:
            - "setuptools_scm": Use setuptools_scm to determine version from git
            - "config": Use version specified in config file
            - "pyproject": Read version from pyproject.toml
            - "git_tags": Extract version from most recent git tag
            Default: "setuptools_scm"
    """

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = True
    tag_format: str = "v{version}"
    tag_prefix: str = ""
    require_clean_working_tree: bool = True
    version_source: Literal["setuptools_scm", "config", "pyproject", "git_tags"] = "setuptools_scm"


class PathsConfig(BaseModel):
    """Path configuration."""

    dist_dir: str = "dist"
    tests_dir: str = "tests"
    src_dir: str = "src"


class DepsConfig(BaseModel):
    """Dependency configuration."""

    requirements: str = "requirements.txt"
    dev_requirements: str = "requirements-dev.txt"
    freeze_output: str = "requirements-freeze.txt"


class DevflowConfig(BaseModel):
    """Main devflow configuration."""

    venv_dir: str = ".venv"
    default_python: str = "python3"
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"
    auto_discover_tasks: bool = True

    paths: PathsConfig = Field(default_factory=PathsConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    deps: DepsConfig = Field(default_factory=DepsConfig)

    # Allow custom tasks and other fields
    model_config = {"extra": "allow"}
