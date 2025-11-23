"""Configuration file loading for devflow."""

import sys
from pathlib import Path
from typing import Any

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def load_config(project_root: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Load devflow configuration from TOML files.
    
    Config discovery order:
    1. Explicit config_path if provided
    2. [tool.devflow] in pyproject.toml
    3. devflow.toml in project root
    4. Empty config (defaults)
    
    Args:
        project_root: Project root directory
        config_path: Optional explicit config file path
        
    Returns:
        Configuration dictionary
    """
    config: dict[str, Any] = {}
    
    # Try explicit config path first
    if config_path is not None:
        if config_path.exists():
            with open(config_path, 'rb') as f:
                loaded = tomllib.load(f)
                # Handle both [tool.devflow] and [devflow] sections
                if 'tool' in loaded and 'devflow' in loaded['tool']:
                    config = loaded['tool']['devflow']
                elif 'devflow' in loaded:
                    config = loaded['devflow']
                else:
                    config = loaded
        return config
    
    # Try pyproject.toml
    pyproject_path = project_root / 'pyproject.toml'
    if pyproject_path.exists():
        with open(pyproject_path, 'rb') as f:
            pyproject = tomllib.load(f)
            if 'tool' in pyproject and 'devflow' in pyproject['tool']:
                config = pyproject['tool']['devflow']
                return config
    
    # Try devflow.toml
    devflow_toml_path = project_root / 'devflow.toml'
    if devflow_toml_path.exists():
        with open(devflow_toml_path, 'rb') as f:
            loaded = tomllib.load(f)
            # Handle both [tool.devflow] and root-level config
            if 'tool' in loaded and 'devflow' in loaded['tool']:
                config = loaded['tool']['devflow']
            elif 'devflow' in loaded:
                config = loaded['devflow']
            else:
                # Treat entire file as config (root-level keys)
                config = loaded
        return config
    
    # Return empty config if no files found
    return config
