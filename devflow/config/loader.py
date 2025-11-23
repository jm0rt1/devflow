"""Configuration loading logic for devflow."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from devflow.config.schema import DevflowConfig, get_default_config


def load_config(
    project_root: Path,
    config_path: Optional[Path] = None,
) -> DevflowConfig:
    """
    Load configuration from TOML files.

    Priority order:
    1. Explicit config_path if provided
    2. [tool.devflow] in pyproject.toml
    3. devflow.toml in project root
    4. Default configuration

    Args:
        project_root: Path to the project root directory
        config_path: Optional explicit path to config file

    Returns:
        DevflowConfig instance with merged configuration
    """
    config_data: Dict[str, Any] = {}

    if config_path:
        # Explicit config file
        if not config_path.exists():
            raise RuntimeError(f"Config file not found: {config_path}")
        config_data = _load_toml_file(config_path)
        # If it's a pyproject.toml, extract [tool.devflow]
        if config_path.name == "pyproject.toml" and "tool" in config_data:
            config_data = config_data.get("tool", {}).get("devflow", {})
    else:
        # Try pyproject.toml first
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            pyproject_data = _load_toml_file(pyproject_path)
            if "tool" in pyproject_data and "devflow" in pyproject_data["tool"]:
                config_data = pyproject_data["tool"]["devflow"]

        # If no config found in pyproject.toml, try devflow.toml
        if not config_data:
            devflow_toml_path = project_root / "devflow.toml"
            if devflow_toml_path.exists():
                config_data = _load_toml_file(devflow_toml_path)

    # Start with default config
    default_config = get_default_config()

    # If we have custom config data, merge it
    if config_data:
        # Merge the configuration
        merged_data = default_config.model_dump()
        _deep_merge(merged_data, config_data)
        return DevflowConfig(**merged_data)

    return default_config


def _load_toml_file(path: Path) -> Dict[str, Any]:
    """Load a TOML file and return its contents."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> None:
    """
    Deep merge override dict into base dict, modifying base in place.

    Args:
        base: Base dictionary to merge into
        override: Override dictionary with values to merge
    """
    for key, value in override.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge(base[key], value)
        else:
            base[key] = value
