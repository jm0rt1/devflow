# devflow

A Python-native project operations CLI that replaces per-project shell scripts with a single, pip-installable command.

## Features

- **Unified CLI**: Single `devflow` command for all project operations
- **Configurable**: Per-project configuration via `pyproject.toml` or `devflow.toml`
- **Portable**: Works on macOS, Linux, and Windows (Git Bash/WSL)
- **Type-safe**: Built with Typer and Pydantic for robust CLI and configuration
- **Extensible**: Support for custom tasks and pipelines

## Installation

```bash
pip install devflow
```

Or install from source for development:

```bash
git clone https://github.com/jm0rt1/devflow.git
cd devflow
pip install -e ".[dev]"
```

## Quick Start

### 1. Configure your project

Add a `[tool.devflow]` section to your `pyproject.toml`:

```toml
[tool.devflow]
venv_dir = ".venv"
test_runner = "pytest"
build_backend = "build"

[tool.devflow.publish]
repository = "pypi"
tag_on_publish = true
tag_format = "v{version}"
require_clean_working_tree = true
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
.venv/bin/pip install pytest build twine
```

### 3. Run commands

```bash
# Run tests
devflow test

# Run tests with arguments
devflow test -- -v -k test_foo

# Build distribution artifacts
devflow build

# Publish to PyPI (with safety checks)
devflow publish

# Dry-run publish to see what would happen
devflow --dry-run publish
```

## Commands

### `devflow test`

Run tests using the configured test runner (pytest by default).

```bash
# Basic usage
devflow test

# Pass arguments to test runner
devflow test -- -v --cov=mypackage

# With verbose output
devflow -v test
```

**Requirements**: Virtual environment must exist with test runner installed.

### `devflow build`

Build distribution artifacts using the configured build backend.

```bash
# Build with dist directory cleanup
devflow build

# Build without cleaning dist/
devflow build --no-clean
```

**Requirements**: Virtual environment must exist with build tools installed.

**Output**: Creates wheel and source distribution in `dist/` directory.

### `devflow publish`

Build and publish package to a package index.

```bash
# Standard publish (runs tests, builds, uploads to PyPI)
devflow publish

# Skip tests before publishing
devflow publish --skip-tests

# Allow dirty working tree
devflow publish --allow-dirty

# Publish to TestPyPI
devflow publish --repository testpypi

# Dry-run to see what would happen
devflow --dry-run publish
```

**Pipeline steps**:
1. Check working tree is clean (unless `--allow-dirty`)
2. Run tests (unless `--skip-tests`)
3. Build package
4. Upload via twine
5. Create git tag (if configured)

## Global Flags

These flags work with any command:

- `--config PATH`: Use custom config file
- `--project-root PATH`: Override project root detection
- `--verbose, -v`: Increase verbosity (can be repeated: `-vv`)
- `--quiet, -q`: Suppress output
- `--dry-run`: Show what would be done without doing it
- `--version`: Show version and exit

## Configuration

Configuration is loaded in priority order:

1. Explicit `--config` path
2. `[tool.devflow]` in `pyproject.toml`
3. `devflow.toml` in project root
4. Built-in defaults

### Configuration Schema

```toml
[tool.devflow]
# Basic settings
venv_dir = ".venv"
default_python = "python3"
build_backend = "build"  # or "hatchling", "poetry-build"
test_runner = "pytest"    # or "unittest", "tox"
package_index = "pypi"

# Path configuration
[tool.devflow.paths]
dist_dir = "dist"
tests_dir = "tests"
src_dir = "src"

# Publish configuration
[tool.devflow.publish]
repository = "pypi"              # or "testpypi"
sign = false                     # Sign with GPG
tag_on_publish = true            # Create git tag on publish
tag_format = "v{version}"        # Tag name format
require_clean_working_tree = true
run_tests_before_publish = true
skip_existing = false            # Skip files already on server

# Dependencies configuration
[tool.devflow.deps]
requirements = "requirements.txt"
dev_requirements = "requirements-dev.txt"
freeze_output = "requirements-freeze.txt"
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=devflow

# Run specific test file
pytest tests/integration/test_build_command.py
```

### Linting

```bash
# Check code style
ruff check devflow/ tests/

# Auto-fix issues
ruff check --fix devflow/ tests/
```

### Building

```bash
# Build package
python -m build
```

## Design

devflow follows the design principles outlined in `docs/DESIGN_SPEC.md`:

- **Python-native**: No shell scripts, pure Python subprocess calls
- **Declarative config**: TOML-based configuration with validation
- **Portable**: Cross-platform support (macOS, Linux, Windows)
- **Safe**: Dry-run mode, working tree checks, proper exit codes
- **Observable**: Structured logging with verbosity control

See `docs/COPILOT_PLAN.md` for implementation details.

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run tests and linting
5. Submit a pull request