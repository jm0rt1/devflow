# devflow

A Python-native project operations CLI that replaces per-project shell scripts with a single, configurable command-line tool.

## Overview

`devflow` replaces scattered shell scripts (`build.sh`, `test.sh`, `publish.sh`, etc.) with a unified CLI that's:
- **Portable**: Works consistently across macOS, Linux, and Git Bash/WSL
- **Configurable**: Define tasks and pipelines in `pyproject.toml` or `devflow.toml`
- **Discoverable**: Rich help text and shell completion support
- **Extensible**: Custom tasks, pipelines, and plugin support

## Installation

```bash
pip install git+https://github.com/jm0rt1/devflow
```

Or for development:
```bash
git clone https://github.com/jm0rt1/devflow
cd devflow
pip install -e .
```

## Quick Start

### 1. Create a configuration file

Add to your `pyproject.toml`:

```toml
[tool.devflow]
venv_dir = ".venv"
default_python = "python3"
test_runner = "pytest"

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]

[tool.devflow.tasks.format]
command = "ruff"
args = ["format"]

[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test"]
```

Or create a standalone `devflow.toml`:

```toml
[devflow]
venv_dir = ".venv"
default_python = "python3"

[devflow.tasks.lint]
command = "ruff"
args = ["check", "."]
```

### 2. Basic usage

```bash
# List available commands and project tasks
devflow

# Create virtual environment
devflow venv init

# Install dependencies
devflow deps sync

# Run tests
devflow test

# Build distribution
devflow build

# Run custom tasks
devflow task lint
devflow task ci-check
```

### 3. Enable shell completion

For **bash**:
```bash
# Add to ~/.bashrc
eval "$(devflow completion bash)"

# Or save to a file
devflow completion bash > ~/.devflow-completion.bash
echo 'source ~/.devflow-completion.bash' >> ~/.bashrc
```

For **zsh**:
```bash
# Add to ~/.zshrc
eval "$(devflow completion zsh)"

# Or save to a file
devflow completion zsh > ~/.devflow-completion.zsh
echo 'source ~/.devflow-completion.zsh' >> ~/.zshrc
```

For **fish**:
```bash
# Save to fish completions directory
devflow completion fish > ~/.config/fish/completions/devflow.fish
```

## Core Commands

- `devflow venv init` - Create and manage virtual environments
- `devflow deps sync` - Install dependencies from requirements files
- `devflow deps freeze` - Freeze installed dependencies
- `devflow test` - Run test suite with configured test runner
- `devflow build` - Build distribution artifacts
- `devflow task <name>` - Run custom tasks defined in config
- `devflow completion <shell>` - Generate shell completion scripts

## Global Options

- `--config PATH` - Specify configuration file path
- `--project-root PATH` - Override project root directory
- `--dry-run` - Show what would be done without executing
- `-v, --verbose` - Increase verbosity (can be repeated: `-vv`)
- `-q, --quiet` - Suppress output except errors
- `--version` - Show version information
- `--help` - Show help for any command

## Configuration

### Configuration Priority

1. Explicit `--config` path
2. `[tool.devflow]` in `pyproject.toml`
3. `devflow.toml` in project root
4. Built-in defaults

### Task Configuration

Define simple command tasks:

```toml
[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]
use_venv = true
```

Define pipeline tasks (run multiple steps in sequence):

```toml
[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test", "build"]
```

### Advanced Configuration

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

[tool.devflow.deps]
requirements = "requirements.txt"
dev_requirements = "requirements-dev.txt"
freeze_output = "requirements-freeze.txt"

[tool.devflow.publish]
repository = "pypi"
tag_on_publish = true
tag_format = "v{version}"
require_clean_working_tree = true
```

## Examples

### Running tests with different verbosity

```bash
# Normal output
devflow test

# Verbose output
devflow test -v

# Very verbose (debug) output
devflow test -vv

# Quiet mode (errors only)
devflow test -q
```

### Custom task pipelines

Define a complete CI pipeline:

```toml
[tool.devflow.tasks.format]
command = "ruff"
args = ["format"]

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]

[tool.devflow.tasks.test]
command = "pytest"
args = ["-v"]

[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test"]
```

Then run:
```bash
devflow task ci-check
```

### Dry-run mode

Preview what would happen without executing:

```bash
devflow --dry-run build
devflow --dry-run task ci-check
```

## Troubleshooting

### Command not found after installation

Ensure your Python user bin directory is in your PATH:

```bash
# For Linux/macOS with user installation
export PATH="$HOME/.local/bin:$PATH"

# Add to ~/.bashrc or ~/.zshrc to make permanent
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Project root not found

`devflow` looks for `pyproject.toml` or `devflow.toml` by walking up from the current directory. Ensure one of these files exists in your project root, or use:

```bash
devflow --project-root /path/to/project <command>
```

### Configuration not loading

Check configuration discovery:

```bash
# Use verbose mode to see which config is loaded
devflow -vv

# Explicitly specify config file
devflow --config devflow.toml
```

### Shell completion not working

#### Bash
Ensure bash-completion is installed:
```bash
# Ubuntu/Debian
sudo apt-get install bash-completion

# macOS
brew install bash-completion
```

Then reload your shell or run:
```bash
source ~/.bashrc
```

#### Zsh
Ensure completion system is initialized in `~/.zshrc`:
```zsh
autoload -Uz compinit
compinit
```

#### Fish
Ensure the completion file is in the right directory:
```bash
mkdir -p ~/.config/fish/completions
devflow completion fish > ~/.config/fish/completions/devflow.fish
```

### Platform-specific issues

#### Windows/Git Bash
- Use forward slashes in paths: `devflow --config ./devflow.toml`
- Ensure Git Bash is up to date
- Some completion features may be limited

#### macOS
- If using system Python, consider using `python3 -m pip` for installation
- Shell completion works best with Homebrew bash/zsh

#### WSL
- Ensure proper line endings (LF, not CRLF) in config files
- Use WSL paths, not Windows paths

## Development

### Running from source

```bash
git clone https://github.com/jm0rt1/devflow
cd devflow
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
pytest -v  # Verbose output
pytest --cov=devflow  # With coverage
```

### Linting and formatting

```bash
ruff check .
ruff format
```

## Design Documentation

For detailed design documentation, see:
- [Design Specification](docs/DESIGN_SPEC.md) - Comprehensive design white paper
- [Implementation Plan](docs/COPILOT_PLAN.md) - Multi-agent implementation strategy

## License

See LICENSE file for details.