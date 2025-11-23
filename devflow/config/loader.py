"""Configuration loader for devflow."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from devflow.config.schema import DevFlowConfig


def load_config(
    project_root: Path,
    config_path: Optional[Path] = None,
) -> DevFlowConfig:
    """
    Load configuration from project root or explicit config path.

    Priority order:
    1. Explicit config_path if provided
    2. [tool.devflow] in pyproject.toml
    3. devflow.toml in project root
    4. Built-in defaults

    Args:
        project_root: Path to project root
        config_path: Optional explicit config path

    Returns:
        DevFlowConfig instance
    """
    config_dict: Dict[str, Any] = {}

    if config_path:
        # Explicit config file
        with open(config_path, "rb") as f:
            data = tomllib.load(f)
            config_dict = data.get("tool", {}).get("devflow", data.get("devflow", {}))
    else:
        # Try pyproject.toml first
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
                if "tool" in data and "devflow" in data["tool"]:
                    config_dict = data["tool"]["devflow"]

        # Try devflow.toml if no config in pyproject.toml
        if not config_dict:
            devflow_toml = project_root / "devflow.toml"
            if devflow_toml.exists():
                with open(devflow_toml, "rb") as f:
                    data = tomllib.load(f)
                    config_dict = data.get("devflow", data)

    # Create config with defaults
    return DevFlowConfig(**config_dict)
