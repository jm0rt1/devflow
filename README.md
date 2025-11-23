# devflow

A Python-native project operations CLI for managing build, test, and deployment workflows.

## Installation

```bash
pip install -e .
```

## Quick Start

Create a `pyproject.toml` in your project root:

```toml
[tool.devflow]
venv_dir = ".venv"

[tool.devflow.tasks.test]
command = "pytest"
args = ["-v"]
use_venv = true

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]
use_venv = true

[tool.devflow.tasks.ci]
pipeline = ["lint", "test"]
```

Then run:

```bash
# Run a single task
devflow task test

# Run a pipeline
devflow task ci

# Dry-run mode
devflow --dry-run task ci

# Verbose output
devflow -v task test
```

## Features

- **Command Framework**: Base classes and registry for extensible commands
- **Task Execution**: Execute single commands or pipelines with proper exit code handling
- **Pipeline Support**: Define composite tasks that run in sequence
- **Cycle Detection**: Automatically detect and prevent circular dependencies
- **Dry-Run Mode**: Preview what would happen without executing commands
- **Verbosity Control**: Adjust output detail with `-v`, `-vv`, or `-q` flags
- **Environment Management**: Tasks can use virtualenv and custom environment variables
- **Exit Code Propagation**: Pipelines stop on first failure with proper exit codes

## Global Options

- `--config PATH`: Specify config file path
- `--project-root PATH`: Specify project root directory
- `--dry-run`: Show what would be done without executing
- `--verbose/-v`: Increase verbosity (can be repeated)
- `--quiet/-q`: Suppress output
- `--version`: Show version

## Task Configuration

Tasks can be defined as either single commands or pipelines:

### Single Command Task

```toml
[tool.devflow.tasks.build]
command = "python"
args = ["-m", "build"]
use_venv = true
env = { "BUILD_ENV" = "production" }
```

### Pipeline Task

```toml
[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test", "build"]
```

## Development

Run tests:

```bash
pytest tests/
```

Run linter:

```bash
ruff check .
```

## Documentation

See `docs/DESIGN_SPEC.md` for the full design specification and `docs/COPILOT_PLAN.md` for the implementation plan.