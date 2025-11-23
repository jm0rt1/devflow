# devflow

A Python-native project operations CLI that replaces per-project shell scripts with a unified, configurable tool.

## Features

- **Virtual Environment Management**: Create and manage project venvs with `devflow venv init`
- **Dependency Management**: Sync and freeze dependencies with `devflow deps sync` and `devflow deps freeze`
- **Configuration-driven**: Configure behavior via `pyproject.toml` or `devflow.toml`
- **Dry-run Support**: Preview operations with `--dry-run` flag
- **Cross-platform**: Works on Linux, macOS, and Windows

## Installation

```bash
pip install -e .
```

Or for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

1. Create a `pyproject.toml` in your project:

```toml
[tool.devflow]
venv_dir = ".venv"
default_python = "python3"

[tool.devflow.deps]
requirements = "requirements.txt"
freeze_output = "requirements-freeze.txt"
```

2. Initialize a virtual environment:

```bash
devflow venv init
```

3. Sync dependencies:

```bash
devflow deps sync
```

4. Freeze dependencies:

```bash
devflow deps freeze
```

## Usage

### Global Options

- `--version`: Show version and exit
- `--config PATH`: Path to config file
- `--project-root PATH`: Path to project root
- `--dry-run`: Show what would be done without doing it
- `--verbose` / `-v`: Increase verbosity (can be repeated)
- `--quiet` / `-q`: Suppress output except errors

### Commands

#### `devflow venv init`

Initialize a virtual environment for the project.

Options:
- `--python PATH`: Python executable to use (overrides config)
- `--recreate`: Recreate venv if it already exists

#### `devflow deps sync`

Install dependencies from requirements files.

#### `devflow deps freeze`

Freeze installed dependencies to a file (deterministic, sorted output).

## Development

Run tests:

```bash
pytest tests/ -v
```

Run linter:

```bash
ruff check .
ruff format .
```

## License

See LICENSE file for details.