"""Configuration schema using Pydantic models."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

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
    tag_prefix: str = ""
    require_clean_working_tree: bool = True


class DepsConfig(BaseModel):
    """Dependencies configuration."""
    
    requirements: str = "requirements.txt"
    dev_requirements: Optional[str] = "requirements-dev.txt"
    freeze_output: str = "requirements-freeze.txt"


class TaskConfig(BaseModel):
    """Task definition."""
    
    command: Optional[str] = None
    args: List[str] = Field(default_factory=list)
    use_venv: bool = True
    env: Dict[str, str] = Field(default_factory=dict)
    pipeline: Optional[List[str]] = None
    steps: Optional[List[str]] = None  # Alias for pipeline


class DevflowConfig(BaseModel):
    """Main devflow configuration."""
    
    # Core settings
    venv_dir: str = ".venv"
    default_python: str = "python3"
    build_backend: str = "build"
    test_runner: str = "pytest"
    package_index: str = "pypi"
    auto_discover_tasks: bool = True
    
    # Sub-configurations
    paths: PathsConfig = Field(default_factory=PathsConfig)
    publish: PublishConfig = Field(default_factory=PublishConfig)
    deps: DepsConfig = Field(default_factory=DepsConfig)
    tasks: Dict[str, TaskConfig] = Field(default_factory=dict)
    
    def get_task(self, name: str) -> Optional[TaskConfig]:
        """Get a task by name."""
        return self.tasks.get(name)
    
    def list_tasks(self) -> List[str]:
        """List all defined task names."""
        return sorted(self.tasks.keys())
