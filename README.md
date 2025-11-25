# devflow

[![CI](https://github.com/jm0rt1/devflow/actions/workflows/ci.yml/badge.svg)](https://github.com/jm0rt1/devflow/actions/workflows/ci.yml)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python-native project operations CLI - replace shell scripts with a unified command for build, test, publish, and more.

## Overview

`devflow` is a Python CLI "orchestrator" for project operations (build, test, publish, etc.):

- **Unified CLI**: One command (`devflow`) replaces scattered shell scripts
- **Per-project configuration**: Declarative TOML config versioned with your code
- **Portable**: Works equivalently on macOS, Linux, and Windows (Git Bash/WSL)
- **Extensible**: Plugin mechanism for custom commands

## Installation

```bash
pip install devflow
```

Or install from source:

```bash
pip install git+https://github.com/jm0rt1/devflow.git
```

## Quick Start

1. Add configuration to your `pyproject.toml`:

```toml
[tool.devflow]
venv_dir = ".venv"
default_python = "python3.11"
test_runner = "pytest"

[tool.devflow.tasks.test]
command = "pytest"
args = ["-q"]
use_venv = true

[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test"]
```

2. Run commands:

```bash
devflow venv init      # Create virtual environment
devflow deps sync      # Install dependencies
devflow test           # Run tests
devflow build          # Build package
devflow publish        # Build and publish (with safety checks)
```

## Commands

| Command | Description |
|---------|-------------|
| `devflow venv init` | Create/manage virtual environment |
| `devflow deps sync` | Install dependencies |
| `devflow deps freeze` | Freeze dependencies to file |
| `devflow test` | Run test suite |
| `devflow build` | Build distribution artifacts |
| `devflow publish` | Build and upload to package index |
| `devflow task <name>` | Run custom task from config |
| `devflow ci-check` | Run CI pipeline (if configured) |

## Global Flags

- `--config PATH` - Specify config file path
- `--project-root PATH` - Override project root detection
- `-v/--verbose` - Increase verbosity (can repeat)
- `-q/--quiet` - Quiet mode
- `--dry-run` - Show what would be done without executing
- `--version` - Show version

## Configuration

Configuration is read from (in order of priority):

1. Explicit `--config` path
2. `[tool.devflow]` section in `pyproject.toml`
3. `devflow.toml` in project root
4. Built-in defaults

See [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md) for full configuration reference.

## Development

```bash
# Clone the repository
git clone https://github.com/jm0rt1/devflow.git
cd devflow

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check .

# Build package
python -m build
```

## License

MIT License - see LICENSE file for details.
