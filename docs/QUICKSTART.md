# Devflow Quickstart Guide

This guide will help you get started with `devflow`, the Python-native CLI for project operations.

## Installation

```bash
pip install devflow
# Or install from source:
pip install git+https://github.com/you/devflow
```

## Basic Usage

After installation, the `devflow` command is available globally:

```bash
devflow --help          # Show all available commands
devflow --version       # Show version
devflow                 # List available commands and project tasks
```

## Project Configuration

`devflow` is configured per-project via TOML. Configuration is discovered in this order:

1. Explicit `--config PATH` flag
2. `[tool.devflow]` section in `pyproject.toml`
3. `devflow.toml` in project root
4. Global defaults from `~/.config/devflow/config.toml`

### Sample Configuration

Add this to your `pyproject.toml`:

```toml
[tool.devflow]
venv_dir = ".venv"
default_python = "python3.11"
build_backend = "build"      # "build" vs "hatchling" vs "poetry-build"
test_runner = "pytest"
package_index = "pypi"       # or "testpypi"

[tool.devflow.paths]
dist_dir = "dist"
tests_dir = "tests"
src_dir = "src"

[tool.devflow.publish]
repository = "pypi"
sign = true
tag_on_publish = true
tag_format = "v{version}"
require_clean_working_tree = true

[tool.devflow.deps]
requirements = "requirements.txt"
dev_requirements = "requirements-dev.txt"
freeze_output = "requirements-freeze.txt"

[tool.devflow.tasks.test]
command = "pytest"
args = ["-q"]
use_venv = true

[tool.devflow.tasks.build]
command = "python"
args = ["-m", "build"]
use_venv = true

[tool.devflow.tasks.publish]
steps = ["build", "upload"]

[tool.devflow.tasks.upload]
command = "twine"
args = ["upload", "dist/*"]
use_venv = true

[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test"]

[tool.devflow.tasks.format]
command = "ruff"
args = ["format"]

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]
```

Or create a standalone `devflow.toml`:

```toml
[devflow]
venv_dir = ".venv"
default_python = "python3.11"

[devflow.tasks.test]
command = "pytest"
args = ["-q"]
use_venv = true
```

## Quick Start Workflow

### 1. Initialize a Virtual Environment

```bash
devflow venv init
# Or with options:
devflow venv init --python python3.12 --recreate
```

### 2. Sync Dependencies

```bash
devflow deps sync
```

### 3. Run Tests

```bash
devflow test
# With additional pytest flags:
devflow test --marker slow --cov
```

### 4. Build Your Package

```bash
devflow build
```

### 5. Publish (with Safety Checks)

```bash
# Preview what would happen:
devflow publish --dry-run

# Actually publish:
devflow publish
```

## Custom Tasks

Define custom tasks in your configuration:

```toml
[tool.devflow.tasks.docs]
command = "sphinx-build"
args = ["-b", "html", "docs/source", "docs/build"]
use_venv = true

[tool.devflow.tasks.format]
command = "ruff"
args = ["format", "."]
```

Run them with:

```bash
devflow task docs
devflow task format
```

## Pipelines

Create composite tasks that run multiple steps:

```toml
[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test"]
```

Run with:

```bash
devflow ci-check
# Or:
devflow task ci-check
```

## Global Flags

These flags work with all commands:

| Flag | Description |
|------|-------------|
| `--config PATH` | Use specific config file |
| `--project-root PATH` | Override project root detection |
| `-v, --verbose` | Increase verbosity (use -vv for debug) |
| `-q, --quiet` | Suppress non-essential output |
| `--dry-run` | Preview actions without executing |
| `--version` | Show devflow version |

## Shell Completion

Enable tab completion for your shell:

```bash
# Bash
eval "$(devflow completion bash)"

# Zsh
eval "$(devflow completion zsh)"

# Fish
devflow completion fish | source
```

See [COMPLETION.md](COMPLETION.md) for permanent installation instructions.

## Next Steps

- Read the full [Design Specification](DESIGN_SPEC.md) for detailed requirements
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for platform-specific issues
- See [COMPLETION.md](COMPLETION.md) for shell completion setup
