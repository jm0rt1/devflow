# devflow

A Python-native project operations CLI that replaces per-project shell scripts with a unified, configurable command-line tool.

## Overview

`devflow` is a CLI orchestrator for project operations like build, test, publish, and more. It's designed to be:

- **Unified**: One command (`devflow`) for all project operations
- **Configurable**: Per-project configuration via TOML
- **Portable**: Works on macOS, Linux, and Windows (Git Bash/WSL)
- **Extensible**: Plugin system for custom commands
- **Python-native**: No brittle shell scripts

## Installation

```bash
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Basic Usage

```bash
# Show help
devflow --help

# Show version
devflow --version

# List available commands
devflow plugin-list
```

### Global Flags

All commands support these global flags:

- `--config PATH` - Path to config file
- `--project-root PATH` - Project root directory
- `--verbose/-v` - Increase verbosity (-v, -vv, etc.)
- `--quiet/-q` - Suppress non-error output
- `--dry-run` - Show what would be done without executing

## Plugin System

`devflow` supports a powerful plugin system for extending functionality.

### Creating a Plugin

```python
# myplugin.py
from devflow.commands.base import Command
from devflow.app import CommandRegistry, AppContext

class MyCommand(Command):
    name = "hello"
    help = "Say hello"
    
    def run(self, **kwargs) -> int:
        self.app.logger.info("Hello from my plugin!")
        return 0

def register(registry: CommandRegistry, app: AppContext) -> None:
    registry.register(MyCommand.name, MyCommand)
```

### Loading Plugins

Two methods for loading plugins:

**1. Entry Points (for distributed packages):**

```toml
# pyproject.toml
[project.entry-points."devflow.plugins"]
myplugin = "mypackage.plugin:register"
```

**2. Config-based (for project-specific plugins):**

```toml
# pyproject.toml
[tool.devflow.plugins]
modules = ["myproject.myplugin"]

# or devflow.toml
[plugins]
modules = ["myproject.myplugin"]
```

See [docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md) for detailed documentation.

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Quality

```bash
ruff check devflow/ tests/
```

## Architecture

- **devflow/** - Main package
  - **app.py** - Application context and command registry
  - **cli.py** - CLI interface using Typer
  - **commands/** - Built-in commands
  - **config/** - Configuration loading
  - **plugins/** - Plugin discovery and loading
- **tests/** - Test suite with fixtures
- **docs/** - Documentation

## Roadmap

This implements **Workstream F** (Plugins & Extensibility) from the development plan. Other workstreams to be implemented:

- Workstream A: Project Bootstrap & App Context ✅ (partial)
- Workstream B: Command Framework & Task Engine
- Workstream C: Venv & Dependency Management
- Workstream D: Test, Build, and Publish Commands
- Workstream E: Git Integration & Safety Rails
- Workstream F: Plugins & Extensibility ✅
- Workstream G: UX, Completion, and Documentation
- Workstream H: CI, Packaging, and Evidence

## Documentation

- [Design Specification](docs/DESIGN_SPEC.md) - Complete design and requirements
- [Development Plan](docs/COPILOT_PLAN.md) - Implementation roadmap
- [Plugin Development](docs/PLUGIN_DEVELOPMENT.md) - Guide for creating plugins

## License

See LICENSE file for details.