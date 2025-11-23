# devflow

A Python-Native Project Operations CLI

[![CI](https://github.com/jm0rt1/devflow/actions/workflows/ci.yml/badge.svg)](https://github.com/jm0rt1/devflow/actions/workflows/ci.yml)

## Overview

`devflow` is a unified CLI tool for managing Python project operations, designed to replace per-project shell scripts with a single, pip-installable command. It provides a consistent interface for:

- Virtual environment management
- Dependency handling (sync, freeze)
- Running tests
- Building packages
- Publishing to package indexes
- Running custom project tasks

## Features

- **Unified CLI**: Single `devflow` command for all project operations
- **Configurable**: Per-project configuration via `pyproject.toml` or `devflow.toml`
- **Portable**: Works on macOS, Linux, and Windows (Git Bash/WSL)
- **Extensible**: Support for custom tasks and pipelines
- **Python-native**: No shell-specific dependencies
- **Dry-run mode**: Preview actions without execution
- **Structured logging**: Configurable verbosity levels

## Installation

### From Source

```bash
git clone https://github.com/jm0rt1/devflow.git
cd devflow
pip install -e .
```

### Development Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```bash
# Show version
devflow --version

# Show help
devflow --help

# Show help for a specific command
devflow test --help
```

### Global Flags

All commands support these global flags:

- `--config PATH`: Path to config file
- `--project-root PATH`: Project root directory
- `--dry-run`: Show what would be done without executing
- `--verbose`, `-v`: Increase verbosity (can be repeated: `-vv`)
- `--quiet`, `-q`: Suppress output
- `--version`: Show version and exit

### Available Commands

- `devflow venv init`: Create/manage virtual environment
- `devflow deps sync`: Install dependencies
- `devflow deps freeze`: Freeze installed packages
- `devflow test`: Run tests
- `devflow build`: Build distribution artifacts
- `devflow publish`: Build and upload to package index
- `devflow task <name>`: Run custom tasks defined in config

## Configuration

Configure `devflow` in your `pyproject.toml`:

```toml
[tool.devflow]
venv_dir = ".venv"
default_python = "python3.11"
build_backend = "build"
test_runner = "pytest"

[tool.devflow.paths]
dist_dir = "dist"
tests_dir = "tests"
src_dir = "src"

[tool.devflow.tasks.test]
command = "pytest"
args = ["-q"]
use_venv = true

[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test", "build"]
```

See [docs/DESIGN_SPEC.md](docs/DESIGN_SPEC.md) for complete configuration options.

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=devflow --cov-report=term-missing

# Run only unit tests
pytest tests/test_*.py

# Run only acceptance tests
pytest tests/acceptance/
```

### Linting and Type Checking

```bash
# Check code style
ruff check .

# Format code
ruff format .

# Type check
mypy devflow
```

### Building

```bash
# Build package
python -m build

# Check distribution
twine check dist/*
```

## CI/CD

The project includes comprehensive CI workflows that test on:

- **Operating Systems**: Ubuntu, macOS, Windows
- **Python Versions**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Test Types**: Unit tests, acceptance tests, integration scenarios

See [.github/workflows/ci.yml](.github/workflows/ci.yml) for details.

## Project Status

This is currently **Workstream H** implementation, focusing on:

- ✅ Package structure with console_scripts entry
- ✅ Runtime and development dependencies
- ✅ CI workflow with cross-platform matrix testing
- ✅ Acceptance test scenarios
- 🚧 Core command implementations (in progress, other workstreams)

See [docs/COPILOT_PLAN.md](docs/COPILOT_PLAN.md) for the complete implementation roadmap.

## Documentation

- [Design Specification](docs/DESIGN_SPEC.md) - Complete design white paper
- [Implementation Plan](docs/COPILOT_PLAN.md) - Multi-agent workstream breakdown

## Requirements

- Python 3.8+
- Dependencies:
  - `typer>=0.9.0` - CLI framework
  - `typing-extensions>=4.0.0` - Type hints backport
  - `tomli>=2.0.0` - TOML parsing (Python <3.11)

## License

MIT

## Contributing

Contributions are welcome! This project follows a multi-workstream implementation plan. Please refer to [docs/COPILOT_PLAN.md](docs/COPILOT_PLAN.md) for the architecture and implementation strategy.