"""Configuration loader for devflow.

Implements configuration discovery order:
1. Explicit --config path if given
2. [tool.devflow] in pyproject.toml
3. devflow.toml in project root
4. User-level default (~/.config/devflow/config.toml) - placeholder hook
5. Built-in defaults
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from devflow.config.defaults import DEFAULT_CONFIG
from devflow.config.schema import DevflowConfig

# Use tomllib for Python 3.11+, fall back to tomli for earlier versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]


def find_config_file(project_root: Path, explicit_config: Path | None = None) -> Path | None:
    """Find the configuration file to use.

    Discovery order:
    1. Explicit --config path if given
    2. pyproject.toml with [tool.devflow] section
    3. devflow.toml in project root
    4. User-level config (~/.config/devflow/config.toml) - placeholder

    Args:
        project_root: The project root directory.
        explicit_config: An explicit config path provided via --config.

    Returns:
        Path to the config file, or None if no config file found.
    """
    # 1. Explicit config path
    if explicit_config is not None:
        if explicit_config.exists():
            return explicit_config
        # Don't fall back if explicit config was specified but doesn't exist
        raise FileNotFoundError(f"Specified config file not found: {explicit_config}")

    # 2. pyproject.toml with [tool.devflow] section
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            data = _parse_toml(pyproject_path)
            if "tool" in data and "devflow" in data["tool"]:
                return pyproject_path
        except Exception:
            pass  # Fall through to next option

    # 3. devflow.toml in project root
    devflow_toml_path = project_root / "devflow.toml"
    if devflow_toml_path.exists():
        return devflow_toml_path

    # 4. User-level config (placeholder hook)
    user_config_path = Path.home() / ".config" / "devflow" / "config.toml"
    if user_config_path.exists():
        return user_config_path

    # No config file found - will use defaults
    return None


def load_config(
    project_root: Path,
    explicit_config: Path | None = None,
) -> DevflowConfig:
    """Load devflow configuration.

    Implements the configuration discovery and merging order:
    1. Start with built-in defaults
    2. Merge user-level config if present
    3. Merge project config (pyproject.toml or devflow.toml)
    4. If explicit --config given, use that instead of project config

    Args:
        project_root: The project root directory.
        explicit_config: An explicit config path provided via --config.

    Returns:
        The merged DevflowConfig.
    """
    config = DEFAULT_CONFIG

    # 1. Try user-level config first (as base layer)
    user_config_path = Path.home() / ".config" / "devflow" / "config.toml"
    if user_config_path.exists():
        try:
            user_data = _load_config_data(user_config_path)
            config = config.merge_with(user_data)
        except Exception:
            pass  # Ignore user config errors, continue with defaults

    # 2. Load project-level config
    if explicit_config is not None:
        # Use explicit config
        if not explicit_config.exists():
            raise FileNotFoundError(f"Specified config file not found: {explicit_config}")
        project_data = _load_config_data(explicit_config)
        config = config.merge_with(project_data)
    else:
        # Try pyproject.toml first
        pyproject_path = project_root / "pyproject.toml"
        if pyproject_path.exists():
            try:
                data = _parse_toml(pyproject_path)
                if "tool" in data and "devflow" in data["tool"]:
                    config = config.merge_with(data["tool"]["devflow"])
                    return config
            except Exception:
                pass  # Fall through to devflow.toml

        # Try devflow.toml
        devflow_toml_path = project_root / "devflow.toml"
        if devflow_toml_path.exists():
            data = _parse_toml(devflow_toml_path)
            # devflow.toml may have [devflow] section or be flat
            if "devflow" in data:
                config = config.merge_with(data["devflow"])
            else:
                config = config.merge_with(data)

    return config


def _parse_toml(path: Path) -> dict[str, Any]:
    """Parse a TOML file and return its contents as a dictionary."""
    if tomllib is None:
        raise ImportError(
            "TOML parsing requires Python 3.11+ or the 'tomli' package. "
            "Install with: pip install tomli"
        )

    with open(path, "rb") as f:
        return tomllib.load(f)


def _load_config_data(path: Path) -> dict[str, Any]:
    """Load configuration data from a file.

    Handles both pyproject.toml (with [tool.devflow]) and devflow.toml formats.
    """
    data = _parse_toml(path)

    # Check if this is a pyproject.toml with [tool.devflow]
    if "tool" in data and "devflow" in data["tool"]:
        return data["tool"]["devflow"]

    # Check if this is a devflow.toml with [devflow] section
    if "devflow" in data:
        return data["devflow"]

    # Assume flat structure
    return data
