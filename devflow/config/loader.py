"""Configuration loader with support for multiple sources and merging."""

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from .schema import DevflowConfig


def load_toml_file(path: Path) -> dict[str, Any]:
    """Load TOML file and return parsed data."""
    with open(path, "rb") as f:
        return tomllib.load(f)


def load_config(
    config_path: Path | None = None,
    project_root: Path | None = None,
) -> DevflowConfig:
    """
    Load configuration with proper precedence order.

    Priority order:
    1. Explicit config_path if provided
    2. [tool.devflow] in pyproject.toml in project root
    3. devflow.toml in project root
    4. Built-in defaults

    Args:
        config_path: Explicit path to config file (highest priority).
        project_root: Project root directory. If None, will be detected.

    Returns:
        Loaded and merged DevflowConfig.
    """
    # Start with defaults
    config = DevflowConfig.get_defaults()

    # If explicit config path provided, use only that
    if config_path:
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        data = load_toml_file(config_path)

        # Handle both [tool.devflow] and [devflow] sections
        config_data = data.get("tool", {}).get("devflow", data.get("devflow", {}))
        if config_data:
            config = config.merge_with(config_data)
        return config

    # Use project root if provided, otherwise try to detect
    if project_root is None:
        from devflow.core.paths import find_project_root

        try:
            project_root = find_project_root()
        except RuntimeError:
            # No project root found, use defaults
            return config

    # Try loading from pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        data = load_toml_file(pyproject_path)
        config_data = data.get("tool", {}).get("devflow")
        if config_data:
            config = config.merge_with(config_data)
            return config

    # Try loading from devflow.toml
    devflow_toml_path = project_root / "devflow.toml"
    if devflow_toml_path.exists():
        data = load_toml_file(devflow_toml_path)
        config_data = data.get("devflow", data)  # Support both [devflow] section and root
        if config_data:
            config = config.merge_with(config_data)

    return config
