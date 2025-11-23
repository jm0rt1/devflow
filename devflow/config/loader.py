"""Configuration loading from TOML files."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from devflow.config.schema import DevflowConfig, TaskConfig


def load_toml(path: Path) -> Dict[str, Any]:
    """Load a TOML file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(
    project_root: Path,
    config_path: Optional[Path] = None
) -> DevflowConfig:
    """
    Load devflow configuration with priority order:
    1. Explicit config_path if provided
    2. [tool.devflow] in pyproject.toml
    3. devflow.toml in project root
    4. Default configuration
    
    Args:
        project_root: Project root directory
        config_path: Optional explicit config file path
        
    Returns:
        Loaded DevflowConfig
    """
    config_data: Dict[str, Any] = {}
    
    # Try explicit config path first
    if config_path and config_path.exists():
        toml_data = load_toml(config_path)
        # Handle both [tool.devflow] and top-level [devflow]
        config_data = toml_data.get("tool", {}).get("devflow", toml_data.get("devflow", {}))
    
    # Try pyproject.toml
    elif (project_root / "pyproject.toml").exists():
        toml_data = load_toml(project_root / "pyproject.toml")
        config_data = toml_data.get("tool", {}).get("devflow", {})
    
    # Try devflow.toml
    elif (project_root / "devflow.toml").exists():
        toml_data = load_toml(project_root / "devflow.toml")
        config_data = toml_data.get("devflow", toml_data)
    
    # Normalize task configurations
    if "tasks" in config_data:
        normalized_tasks = {}
        for task_name, task_data in config_data["tasks"].items():
            if isinstance(task_data, dict):
                # Handle 'steps' as alias for 'pipeline'
                if "steps" in task_data and "pipeline" not in task_data:
                    task_data["pipeline"] = task_data["steps"]
                normalized_tasks[task_name] = task_data
        config_data["tasks"] = normalized_tasks
    
    return DevflowConfig(**config_data)
