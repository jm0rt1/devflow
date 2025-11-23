# Devflow Git Integration - Quick Reference

## Installation
```bash
pip install -e ".[dev]"
```

## Common Use Cases

### 1. Check Working Tree Status
```python
from devflow.core.git import is_working_tree_clean, require_clean_working_tree

# Check if clean
if is_working_tree_clean():
    print("✓ Safe to proceed")

# Require clean or raise error
try:
    require_clean_working_tree()
except DirtyWorkingTreeError as e:
    print(f"✗ {e}")
```

### 2. Create Release Tags
```python
from devflow.core.git import format_tag, create_tag

# Format a tag
tag = format_tag("1.2.3", tag_format="v{version}")  # "v1.2.3"

# Create tag (idempotent)
if create_tag(tag, message="Release 1.2.3"):
    print(f"✓ Created {tag}")
else:
    print(f"ℹ {tag} already exists")

# Dry-run mode
create_tag("v2.0.0", dry_run=True)  # Preview only
```

### 3. Get Current Version
```python
from devflow.core.git import get_current_version

# Try setuptools_scm first, fall back to config
version = get_current_version(
    version_source="setuptools_scm",
    fallback_version="0.1.0"
)
print(f"Version: {version}")

# Use git tags
version = get_current_version(version_source="git_tags")
```

### 4. Custom Version Patterns
```python
from devflow.core.git import get_version_from_git_tags

# Extract date-based version
version = get_version_from_git_tags(
    version_pattern=r"(\d{8})"  # Matches YYYYMMDD
)
```

## Configuration

### pyproject.toml
```toml
[tool.devflow.publish]
require_clean_working_tree = true
tag_on_publish = true
tag_format = "v{version}"
tag_prefix = ""
version_source = "setuptools_scm"  # or "git_tags", "config", "pyproject"
```

## API Reference

### Status Checks
| Function | Purpose | Returns |
|----------|---------|---------|
| `is_git_repository(path)` | Check if inside git repo | bool |
| `is_working_tree_clean(path)` | Check for uncommitted changes | bool |
| `require_clean_working_tree(path, message)` | Enforce clean tree | None (raises on dirty) |

### Tag Management
| Function | Purpose | Returns |
|----------|---------|---------|
| `format_tag(version, tag_format, tag_prefix)` | Format version into tag | str |
| `tag_exists(tag_name, path)` | Check if tag exists | bool |
| `create_tag(tag_name, message, path, force, dry_run)` | Create tag | bool (True if created) |

### Version Discovery
| Function | Purpose | Returns |
|----------|---------|---------|
| `get_version_from_setuptools_scm(path)` | Get version via setuptools_scm | str or None |
| `get_version_from_git_tags(path, version_pattern)` | Extract from latest tag | str or None |
| `get_current_version(path, version_source, fallback_version)` | Multi-source version | str |

### Utilities
| Function | Purpose | Returns |
|----------|---------|---------|
| `run_git_command(args, cwd, check, capture_output)` | Run git command | CompletedProcess |
| `get_current_commit_hash(path, short)` | Get commit hash | str |

## Error Handling

### GitError
Base exception for git operations
```python
try:
    run_git_command(["invalid-command"])
except GitError as e:
    print(f"Git error: {e}")
```

### DirtyWorkingTreeError
Raised when working tree is dirty
```python
try:
    require_clean_working_tree()
except DirtyWorkingTreeError as e:
    print(f"Cannot proceed: {e}")
    # Suggests: Commit or stash changes, or use --allow-dirty
```

## Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Git Tests Only
```bash
pytest tests/test_git.py -v
```

### Coverage Report
```bash
pytest tests/ --cov=devflow --cov-report=term-missing
```

## Examples

### Safe Publish Flow
```python
from devflow.core.git import require_clean_working_tree, create_tag, format_tag

def safe_publish(version: str, config):
    # 1. Ensure clean working tree
    if config.require_clean_working_tree:
        require_clean_working_tree()
    
    # 2. Build and upload (not shown)
    build_and_upload()
    
    # 3. Create tag
    if config.tag_on_publish:
        tag = format_tag(version, config.tag_format, config.tag_prefix)
        create_tag(tag, message=f"Release {version}")
```

### Version-Aware CLI
```python
from devflow.core.git import get_current_version

def show_version(config):
    version = get_current_version(
        version_source=config.publish.version_source,
        fallback_version="0.1.0"
    )
    print(f"devflow version {version}")
```

## Best Practices

1. **Always use shell=False**: All git commands use explicit arg lists
2. **Enable dry-run**: Preview changes before executing
3. **Idempotent operations**: Safe to run multiple times
4. **Clear error messages**: Suggest remediation steps
5. **Test with temp repos**: Use fixtures for integration tests

## Troubleshooting

### "Git executable not found"
- Install git: `sudo apt-get install git` (Linux) or `brew install git` (macOS)

### "Working tree not clean"
- Commit changes: `git add . && git commit -m "message"`
- Or stash: `git stash`
- Or use `--allow-dirty` flag (if available)

### "Could not determine version"
- Add git tags: `git tag v0.1.0`
- Or provide fallback: `fallback_version="0.1.0"`
- Or install setuptools_scm: `pip install setuptools-scm`

## Links

- [Full Documentation](devflow/core/README_GIT.md)
- [Implementation Summary](WORKSTREAM_E_SUMMARY.md)
- [Design Spec](docs/DESIGN_SPEC.md)
- [Implementation Plan](docs/COPILOT_PLAN.md)
