# Git Integration Module

This module provides git integration helpers for devflow, implementing Workstream E from the COPILOT_PLAN.md.

## Features

### Status Checks
- `is_git_repository(path)`: Check if a path is inside a git repository
- `is_working_tree_clean(path)`: Check if the working tree has uncommitted changes
- `require_clean_working_tree(path, message)`: Enforce clean working tree or raise error

### Tag Management
- `format_tag(version, tag_format, tag_prefix)`: Format version strings into git tags
- `tag_exists(tag_name, path)`: Check if a tag exists
- `create_tag(tag_name, message, path, force, dry_run)`: Create git tags with idempotent behavior

### Version Discovery
- `get_version_from_setuptools_scm(path)`: Get version using setuptools_scm
- `get_version_from_git_tags(path)`: Extract version from latest git tag
- `get_current_version(path, version_source, fallback_version)`: Get version from various sources

### Utilities
- `run_git_command(args, cwd, check, capture_output)`: Run git commands with explicit arg lists
- `get_current_commit_hash(path, short)`: Get current commit hash

## Configuration

The git module respects configuration from `devflow.config.schema.PublishConfig`:

```python
publish:
  require_clean_working_tree: bool = True
  tag_on_publish: bool = True
  tag_format: str = "v{version}"
  tag_prefix: str = ""
  version_source: Literal["setuptools_scm", "config", "pyproject", "git_tags"] = "setuptools_scm"
```

## Usage Examples

### Check Working Tree Status
```python
from devflow.core.git import is_working_tree_clean, require_clean_working_tree

# Check if clean
if is_working_tree_clean():
    print("Working tree is clean")

# Require clean tree (raises DirtyWorkingTreeError if dirty)
require_clean_working_tree(message="Commit your changes before publishing")
```

### Create Git Tags
```python
from devflow.core.git import create_tag, format_tag

# Format a tag name
tag = format_tag("1.0.0", tag_format="v{version}")  # "v1.0.0"

# Create a lightweight tag
create_tag("v1.0.0")

# Create an annotated tag
create_tag("v1.0.0", message="Release 1.0.0")

# Dry-run mode (doesn't actually create tag)
create_tag("v1.0.0", dry_run=True)

# Idempotent: returns False if tag already exists
result = create_tag("v1.0.0")  # False if already exists
```

### Get Current Version
```python
from devflow.core.git import get_current_version

# Try setuptools_scm first (default)
version = get_current_version()

# Use git tags
version = get_current_version(version_source="git_tags")

# Use config fallback
version = get_current_version(version_source="config", fallback_version="0.1.0")
```

## Design Principles

1. **Shell=False**: All git commands use explicit argument lists, never shell=True
2. **Dry-run Support**: Commands that modify state support --dry-run mode
3. **Idempotent Operations**: Tag creation is idempotent (safe to call multiple times)
4. **Clear Error Messages**: Provides helpful error messages when operations fail
5. **Type Safety**: Uses type hints throughout
6. **Portable**: Works on macOS, Linux, and Windows Git Bash

## Testing

The module includes comprehensive tests in `tests/test_git.py`:
- Unit tests for all functions
- Integration tests using temporary git repositories
- Tests for dirty working tree blocking
- Tests for idempotent tag creation
- Tests for version discovery from multiple sources

Run tests with:
```bash
pytest tests/test_git.py -v
```
