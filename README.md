# devflow

A Python-native project operations CLI that replaces per-project shell scripts with a unified, configurable tool.

## Status

**Current Implementation: Workstream A (Bootstrap & App Context)** ✅

This implementation provides the foundation for the devflow CLI:
- Package layout and structure
- Project root detection
- Configuration discovery and merging
- Typed configuration schema
- AppContext with structured logging
- CLI with global flags and stub commands

## Installation

```bash
# Install in development mode
pip install -e ".[dev]"
```

## Usage

```bash
# Show help
devflow --help

# Show version
devflow --version

# Use verbose mode
devflow -v test

# Use dry-run mode
devflow --dry-run publish

# Use custom config file
devflow --config custom.toml test

# Use custom project root
devflow --project-root /path/to/project test
```

## Configuration

devflow supports configuration in multiple locations with proper precedence:

1. Explicit `--config` path (highest priority)
2. `[tool.devflow]` section in `pyproject.toml`
3. `devflow.toml` in project root
4. Built-in defaults

Example configuration in `pyproject.toml`:

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

[tool.devflow.publish]
repository = "pypi"
sign = false
tag_on_publish = false

[tool.devflow.tasks.test]
command = "pytest"
args = ["-v"]
use_venv = true
```

See `tests/fixtures/sample-config.toml` for a complete configuration example.

## Available Commands

- `venv` - Manage project virtual environment
- `deps` - Manage dependencies (sync, freeze)
- `test` - Run tests
- `build` - Build distribution artifacts
- `publish` - Build and upload to package index
- `git` - Git-related helper commands
- `task` - Run custom tasks defined in config

**Note**: Commands are currently stubs and will be fully implemented in subsequent workstreams.

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Run tests with coverage
pytest tests/ --cov=devflow --cov-report=term-missing

# Run linter
ruff check devflow/ tests/

# Auto-fix linting issues
ruff check --fix devflow/ tests/
```

## Architecture

See `docs/DESIGN_SPEC.md` and `docs/COPILOT_PLAN.md` for detailed design and implementation plans.

## Testing

The implementation includes comprehensive unit tests:
- Project root detection
- Configuration loading and merging
- CLI interface and global flags
- AppContext and logging

Current test coverage: **87%** (22 tests passing)

## Next Steps

Future workstreams will implement:
- **Workstream B**: Command framework and task engine
- **Workstream C**: Venv and dependency management
- **Workstream D**: Test, build, and publish commands
- **Workstream E**: Git integration
- **Workstream F**: Plugin system
- **Workstream G**: UX and completion
- **Workstream H**: CI and packaging