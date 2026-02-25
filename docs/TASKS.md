# How to Define Tasks in devflow

This guide explains how to define custom tasks and pipelines in your devflow configuration.

## Basic Task Definition

Tasks are defined in the `[tool.devflow.tasks]` section of your `pyproject.toml` or in `devflow.toml`.

### Simple Task

A simple task runs a single command:

```toml
[tool.devflow.tasks.test]
command = "pytest"
args = ["-q", "--tb=short"]
use_venv = true
```

### Task Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `command` | string | required | The command to execute |
| `args` | list[string] | `[]` | Arguments to pass to the command |
| `use_venv` | bool | `true` | Whether to use the project's virtual environment |
| `env` | dict | `null` | Environment variables to set |
| `working_dir` | string | `null` | Working directory (relative to project root) |

### Example with Environment Variables

```toml
[tool.devflow.tasks.debug-test]
command = "pytest"
args = ["-v", "--tb=long"]
use_venv = true
env = { PYTHONDONTWRITEBYTECODE = "1", DEBUG = "true" }
```

### Example with Working Directory

```toml
[tool.devflow.tasks.frontend-build]
command = "npm"
args = ["run", "build"]
use_venv = false
working_dir = "frontend"
```

## Pipeline Definition

Pipelines run multiple tasks in sequence. If any task fails, the pipeline stops (short-circuits).

### Basic Pipeline

```toml
[tool.devflow.tasks.ci-check]
pipeline = ["lint", "test", "build"]
```

This requires that `lint`, `test`, and `build` tasks are also defined.

### Complete Example

```toml
# Individual tasks
[tool.devflow.tasks.format]
command = "ruff"
args = ["format", "."]

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]

[tool.devflow.tasks.test]
command = "pytest"
args = ["-q"]

[tool.devflow.tasks.build]
command = "python"
args = ["-m", "build"]

# Pipeline combining tasks
[tool.devflow.tasks.ci-check]
pipeline = ["format", "lint", "test"]

[tool.devflow.tasks.release]
pipeline = ["ci-check", "build"]
```

## Running Tasks

Use the `devflow task` command to run tasks:

```bash
# Run a single task
devflow task test

# Run a pipeline
devflow task ci-check

# List available tasks
devflow task --list

# Dry-run (show what would be executed)
devflow --dry-run task ci-check
```

## Exit Codes

- `0`: Success
- `1`: Task error or configuration error
- `126`: Permission denied (command not executable)
- `127`: Command not found

For pipelines, the exit code is that of the first failing task.

## Cycle Detection

devflow detects cycles in pipeline definitions and will report an error:

```toml
# This will cause a "cycle detected" error
[tool.devflow.tasks.a]
pipeline = ["b"]

[tool.devflow.tasks.b]
pipeline = ["a"]
```

## Best Practices

1. **Use descriptive task names**: `lint`, `test`, `build`, `ci-check`
2. **Set `use_venv = false`** for non-Python tools
3. **Keep pipelines flat** when possible to simplify debugging
4. **Use environment variables** for configuration that varies between environments
5. **Test tasks with `--dry-run`** before running them for real
