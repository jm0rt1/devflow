# CLI Help Text Examples

This document provides examples of `devflow` CLI help output and usage patterns.

## Top-Level Help

```bash
$ devflow --help
Usage: devflow [OPTIONS] COMMAND [ARGS]...

  Devflow - Python-native project operations CLI.

  Replace per-project shell scripts with a single, configurable command.

Options:
  --config PATH         Path to configuration file
  --project-root PATH   Override project root detection
  -v, --verbose         Increase verbosity (use -vv for debug)
  -q, --quiet           Suppress non-essential output
  --dry-run             Preview actions without executing
  --version             Show version and exit
  --help                Show this message and exit

Commands:
  venv       Manage project virtual environment
  deps       Manage dependencies (sync, freeze)
  test       Run tests using configured test runner
  build      Build distribution artifacts
  publish    Build and upload to package index
  task       Run custom tasks defined in config
  ci-check   Run CI pipeline (lint, test, build)
  completion Generate shell completion script
```

## Running With No Arguments

When you run `devflow` without any arguments in a project directory, it displays available commands and project-specific tasks:

```bash
$ devflow
Devflow v0.1.0

Available Commands:
  venv       Manage project virtual environment
  deps       Manage dependencies (sync, freeze)
  test       Run tests using configured test runner
  build      Build distribution artifacts
  publish    Build and upload to package index
  task       Run custom tasks defined in config
  ci-check   Run CI pipeline (lint, test, build)
  completion Generate shell completion script

Project Tasks (from pyproject.toml):
  docs       Build documentation with sphinx
  lint       Run ruff linter
  format     Format code with ruff
  typecheck  Run mypy type checker

Run 'devflow --help' for more options.
Run 'devflow <command> --help' for command-specific help.
```

---

## Command-Specific Help

### Virtual Environment Commands

```bash
$ devflow venv --help
Usage: devflow venv [OPTIONS] COMMAND [ARGS]...

  Manage project virtual environment.

Commands:
  init  Create or recreate the virtual environment
```

```bash
$ devflow venv init --help
Usage: devflow venv init [OPTIONS]

  Create or recreate the virtual environment.

  Creates a virtual environment at the configured venv_dir (default: .venv)
  using the configured default_python.

Options:
  --python PATH   Python interpreter to use (overrides config)
  --recreate      Delete and recreate existing venv
  --help          Show this message and exit

Examples:
  # Create venv with default settings
  devflow venv init

  # Create venv with specific Python version
  devflow venv init --python python3.12

  # Force recreate existing venv
  devflow venv init --recreate

  # Preview what would happen
  devflow --dry-run venv init
```

### Dependency Commands

```bash
$ devflow deps --help
Usage: devflow deps [OPTIONS] COMMAND [ARGS]...

  Manage dependencies (sync, freeze).

Commands:
  sync   Install dependencies from requirements files
  freeze Freeze installed packages to file
```

```bash
$ devflow deps sync --help
Usage: devflow deps sync [OPTIONS]

  Install dependencies from requirements files.

  Installs packages from configured requirements files into the venv.

Options:
  --dev       Include development dependencies
  --extras    Install optional extras
  --help      Show this message and exit

Examples:
  # Sync base dependencies
  devflow deps sync

  # Sync including dev dependencies
  devflow deps sync --dev

  # Preview sync without installing
  devflow --dry-run deps sync
```

```bash
$ devflow deps freeze --help
Usage: devflow deps freeze [OPTIONS]

  Freeze installed packages to file.

  Writes currently installed packages to the configured freeze_output file.

Options:
  --output PATH  Output file (overrides config)
  --help         Show this message and exit

Examples:
  # Freeze to configured file (default: requirements-freeze.txt)
  devflow deps freeze

  # Freeze to specific file
  devflow deps freeze --output requirements-lock.txt
```

### Test Command

```bash
$ devflow test --help
Usage: devflow test [OPTIONS] [ARGS]...

  Run tests using configured test runner.

  Executes the configured test runner (default: pytest) with optional
  pass-through arguments.

Options:
  --pattern TEXT  Test file pattern
  --marker TEXT   Run tests matching marker expression
  --cov           Enable coverage reporting
  --help          Show this message and exit

Additional arguments are passed through to the test runner.

Examples:
  # Run all tests
  devflow test

  # Run tests matching a pattern
  devflow test --pattern "test_api*"

  # Run tests with specific marker
  devflow test --marker "not slow"

  # Run with coverage
  devflow test --cov

  # Pass additional pytest arguments
  devflow test -- -x --tb=short

  # Dry run to see what would execute
  devflow --dry-run test
```

### Build Command

```bash
$ devflow build --help
Usage: devflow build [OPTIONS]

  Build distribution artifacts.

  Builds wheel and sdist using the configured build backend
  (default: python -m build).

Options:
  --clean       Clean dist directory before building
  --wheel-only  Build wheel only (no sdist)
  --sdist-only  Build sdist only (no wheel)
  --help        Show this message and exit

Examples:
  # Build wheel and sdist
  devflow build

  # Clean and build
  devflow build --clean

  # Build wheel only
  devflow build --wheel-only

  # Preview build command
  devflow --dry-run build
```

### Publish Command

```bash
$ devflow publish --help
Usage: devflow publish [OPTIONS]

  Build and upload to package index.

  Complete publish workflow:
  1. Verify working tree is clean (unless --allow-dirty)
  2. Run tests (unless --skip-tests)
  3. Build distribution artifacts
  4. Upload to configured repository
  5. Create git tag (if configured)

Options:
  --repository TEXT  Target repository (default: pypi)
  --allow-dirty      Publish with uncommitted changes
  --skip-tests       Skip pre-publish tests
  --skip-build       Use existing dist artifacts
  --help             Show this message and exit

Examples:
  # Full publish workflow
  devflow publish

  # Publish to TestPyPI
  devflow publish --repository testpypi

  # Preview publish (RECOMMENDED first)
  devflow --dry-run publish

  # Publish with uncommitted changes (not recommended)
  devflow publish --allow-dirty

  # Publish skipping tests
  devflow publish --skip-tests
```

### Task Command

```bash
$ devflow task --help
Usage: devflow task [OPTIONS] NAME [ARGS]...

  Run custom tasks defined in config.

  Executes a task defined in [tool.devflow.tasks.<name>] section.
  Tasks can be single commands or pipelines of multiple steps.

Arguments:
  NAME  Name of the task to run

Options:
  --help  Show this message and exit

Examples:
  # Run a custom task
  devflow task docs

  # Run a pipeline task
  devflow task ci-check

  # Preview task execution
  devflow --dry-run task lint

  # Run task with additional arguments
  devflow task lint -- --fix
```

### CI-Check Command

```bash
$ devflow ci-check --help
Usage: devflow ci-check [OPTIONS]

  Run CI pipeline (lint, test, build).

  Executes the configured ci-check pipeline. If not configured,
  runs default steps: format check, lint, test.

  Pipeline stops on first failure and reports the failing step.

Options:
  --continue-on-error  Continue pipeline even if a step fails
  --help               Show this message and exit

Examples:
  # Run full CI pipeline
  devflow ci-check

  # Run CI pipeline with verbose output
  devflow -v ci-check

  # Continue pipeline even if steps fail
  devflow ci-check --continue-on-error

  # Preview CI pipeline steps
  devflow --dry-run ci-check
```

### Completion Command

```bash
$ devflow completion --help
Usage: devflow completion [OPTIONS] SHELL

  Generate shell completion script.

  Output a completion script for the specified shell. The script can be
  evaluated directly or saved to a file for permanent installation.

Arguments:
  SHELL  Shell type: bash, zsh, or fish

Options:
  --help  Show this message and exit

Examples:
  # Generate and eval for current session
  eval "$(devflow completion bash)"
  eval "$(devflow completion zsh)"
  devflow completion fish | source

  # Save to file for permanent installation
  devflow completion bash > ~/.local/share/bash-completion/completions/devflow
  devflow completion zsh > ~/.zsh/completions/_devflow
  devflow completion fish > ~/.config/fish/completions/devflow.fish

See docs/COMPLETION.md for detailed setup instructions.
```

---

## Usage Patterns

### Verbose and Quiet Modes

```bash
# Normal output
$ devflow test
[test] Running pytest...
================================ test session starts ================================
...
================================ 5 passed in 0.23s ==================================

# Verbose output (-v)
$ devflow -v test
[test] Running pytest in /home/user/project/.venv
[test] Command: .venv/bin/pytest -q
================================ test session starts ================================
...

# Debug output (-vv)
$ devflow -vv test
[config] Loading configuration from /home/user/project/pyproject.toml
[config] venv_dir = .venv
[config] test_runner = pytest
[test] Resolved venv: /home/user/project/.venv
[test] Command: ['.venv/bin/pytest', '-q']
[test] Environment: {'PATH': '...', 'VIRTUAL_ENV': '...'}
...

# Quiet mode
$ devflow -q test
5 passed
```

### Dry Run Mode

```bash
$ devflow --dry-run publish
[dry-run] Would check git working tree status
[dry-run] Would run: pytest -q
[dry-run] Would run: python -m build
[dry-run] Would run: twine upload dist/*
[dry-run] Would create git tag: v0.1.0
```

### Combining Flags

```bash
# Verbose dry run
$ devflow -v --dry-run build
[build] Using build backend: python -m build
[build] dist_dir: dist
[dry-run] Would clean dist directory
[dry-run] Would run: ['.venv/bin/python', '-m', 'build']

# Quiet with specific config
$ devflow -q --config custom.toml test
5 passed
```

---

## Configuration Examples in Help

Commands reference configuration options that affect their behavior:

```bash
$ devflow build --help
...
Configuration:
  The build command uses these config options from [tool.devflow]:
  
  build_backend = "build"    # Build tool to use
  [tool.devflow.paths]
  dist_dir = "dist"          # Output directory for artifacts

  [tool.devflow.tasks.build]
  command = "python"         # Override with custom build command
  args = ["-m", "build"]
```

---

## See Also

- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [COMPLETION.md](COMPLETION.md) - Shell completion setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Problem solving
- [DESIGN_SPEC.md](DESIGN_SPEC.md) - Full design specification
