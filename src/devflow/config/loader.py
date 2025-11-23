"""Configuration loading and discovery."""

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from .schema import AppConfig


def load_toml(path: Path) -> dict[str, Any]:
    """Load TOML file."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(
    project_root: Path,
    config_path: Path | None = None,
) -> AppConfig:
    """
    Load configuration from project.

    Priority order:
    1. Explicit config_path if provided
    2. [tool.devflow] in pyproject.toml
    3. devflow.toml in project root
    4. Default config

    Args:
        project_root: Project root directory
        config_path: Explicit config file path

    Returns:
        Loaded and validated configuration
    """
    config_data: dict[str, Any] = {}

    if config_path:
        # Explicit config path provided
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        config_data = load_toml(config_path)
        # Handle both [devflow] and [tool.devflow] sections
        if "tool" in config_data and "devflow" in config_data["tool"]:
            config_data = config_data["tool"]["devflow"]
        elif "devflow" in config_data:
            config_data = config_data["devflow"]
    else:
        # Try pyproject.toml first
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_data = load_toml(pyproject_path)
            if "tool" in pyproject_data and "devflow" in pyproject_data["tool"]:
                config_data = pyproject_data["tool"]["devflow"]

        # Try devflow.toml as fallback
        if not config_data:
            devflow_path = project_root / "devflow.toml"
            if devflow_path.exists():
                devflow_data = load_toml(devflow_path)
                if "devflow" in devflow_data:
                    config_data = devflow_data["devflow"]
                else:
                    config_data = devflow_data

    # Create config with defaults
    return AppConfig.from_dict(config_data)
