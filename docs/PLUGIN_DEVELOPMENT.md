# Plugin Development Guide

This guide explains how to create plugins for `devflow` to extend its functionality with custom commands.

## Overview

Plugins allow you to add new commands to `devflow` without modifying the core codebase. Plugins are discovered via:

1. **Entry points** - Plugins installed as Python packages
2. **Config paths** - Plugin modules specified in configuration files

## Plugin Interface

Every plugin must implement a `register` function with the following signature:

```python
from devflow.app import CommandRegistry, AppContext

def register(registry: CommandRegistry, app: AppContext) -> None:
    """Register plugin commands and perform setup.
    
    Args:
        registry: Command registry to register new commands
        app: Application context with config, logger, etc.
    """
    # Your plugin registration code here
    pass
```

## Creating a Plugin

### Step 1: Define Your Command

Create a command class that extends `Command`:

```python
from devflow.commands.base import Command

class MyCommand(Command):
    """My custom command."""
    
    name = "mycommand"
    help = "Description of what my command does"
    
    def run(self, **kwargs) -> int:
        """Execute the command.
        
        Args:
            **kwargs: Command-specific arguments
            
        Returns:
            Exit code (0 for success, non-zero for failure)
        """
        # Access app context for config, logging, dry-run mode, etc.
        self.app.logger.info("Running my command")
        
        # Support dry-run mode
        if self.app.dry_run:
            self.app.logger.info("[DRY-RUN] Would perform action")
            return 0
        
        # Perform actual work
        # ...
        
        return 0  # Success
```

### Step 2: Implement the Register Function

Create a `register` function that registers your command:

```python
from devflow.app import CommandRegistry, AppContext

def register(registry: CommandRegistry, app: AppContext) -> None:
    """Register plugin commands."""
    registry.register(MyCommand.name, MyCommand)
```

### Complete Plugin Example

```python
"""My devflow plugin - myproject/myplugin.py"""

from devflow.commands.base import Command
from devflow.app import CommandRegistry, AppContext


class MyCommand(Command):
    """My custom command."""
    
    name = "mycommand"
    help = "Description of what my command does"
    
    def run(self, **kwargs) -> int:
        """Execute the command."""
        self.app.logger.info("Running my command")
        
        if self.app.dry_run:
            self.app.logger.info("[DRY-RUN] Would perform action")
            return 0
        
        # Perform actual work
        self.app.logger.info("Command completed successfully")
        return 0


def register(registry: CommandRegistry, app: AppContext) -> None:
    """Register plugin commands."""
    app.logger.debug("Loading myplugin")
    registry.register(MyCommand.name, MyCommand)
```

## Plugin Discovery Methods

### Method 1: Entry Points (Recommended for Packages)

For plugins distributed as Python packages, use setuptools entry points in `pyproject.toml`:

```toml
[project.entry-points."devflow.plugins"]
myplugin = "mypackage.plugin:register"
```

Or in `setup.py`:

```python
setup(
    name="mypackage",
    entry_points={
        "devflow.plugins": [
            "myplugin = mypackage.plugin:register",
        ],
    },
)
```

After installing the package, `devflow` will automatically discover and load the plugin.

### Method 2: Config-Based Loading

For project-specific or development plugins, specify the module path in your config:

**pyproject.toml:**
```toml
[tool.devflow.plugins]
modules = ["myproject.myplugin", "anothermodule.plugin"]
```

**devflow.toml:**
```toml
[plugins]
modules = ["myproject.myplugin", "anothermodule.plugin"]
```

The module must be importable (in PYTHONPATH or installed).

## Plugin Precedence

When a plugin is available from multiple sources, the precedence order is:

1. **Config-defined plugins** (highest priority)
2. **Entry point plugins**

This allows projects to override installed plugins with custom implementations.

## Error Handling

Plugins should handle errors gracefully. If a plugin fails to load or register:

- The error is logged as a warning
- Other plugins continue to load
- Core `devflow` functionality remains available

**Example of error handling in plugin:**

```python
def register(registry: CommandRegistry, app: AppContext) -> None:
    """Register plugin commands with error handling."""
    try:
        # Verify dependencies or configuration
        if not some_required_condition():
            app.logger.warning("Skipping myplugin: requirement not met")
            return
        
        registry.register(MyCommand.name, MyCommand)
        app.logger.debug("Successfully loaded myplugin")
        
    except Exception as e:
        app.logger.error(f"Failed to register myplugin: {e}")
        # Don't re-raise - let devflow continue
```

## Best Practices

### 1. Support Global Flags

Always respect the application context flags:

```python
def run(self, **kwargs) -> int:
    # Support dry-run
    if self.app.dry_run:
        self.app.logger.info("[DRY-RUN] Would perform action")
        return 0
    
    # Respect verbosity
    if self.app.verbose >= 2:
        self.app.logger.debug("Detailed debug information")
    
    # Support quiet mode (logger handles this automatically)
    self.app.logger.info("Normal output")
```

### 2. Use Structured Logging

Use the app's logger with appropriate log levels:

```python
self.app.logger.debug("Detailed debugging info")
self.app.logger.info("Normal user-facing messages")
self.app.logger.warning("Non-fatal issues")
self.app.logger.error("Errors that prevent completion")
```

### 3. Return Proper Exit Codes

- Return `0` for success
- Return non-zero for failures
- Use standard exit codes where applicable (e.g., 1 for general errors, 2 for misuse)

### 4. Access Configuration

Read configuration from the app context:

```python
def run(self, **kwargs) -> int:
    # Get plugin-specific config
    plugin_config = self.app.config.get('myplugin', {})
    option = plugin_config.get('some_option', 'default')
    
    # Use the config
    self.app.logger.info(f"Using option: {option}")
    return 0
```

### 5. Document Your Plugin

Include docstrings and help text:

```python
class MyCommand(Command):
    """Brief description of what the command does.
    
    Longer explanation with usage examples:
    
        devflow mycommand --option value
        devflow mycommand --help
    """
    
    name = "mycommand"
    help = "Brief help text shown in command listing"
```

## Testing Plugins

Create tests for your plugin:

```python
import pytest
from devflow.app import AppContext, CommandRegistry
from mypackage.plugin import MyCommand, register


def test_plugin_registration():
    """Test that plugin registers correctly."""
    app = AppContext(
        project_root=Path.cwd(),
        config={},
    )
    registry = CommandRegistry()
    
    register(registry, app)
    
    assert registry.get("mycommand") is not None


def test_command_execution():
    """Test command runs successfully."""
    app = AppContext(
        project_root=Path.cwd(),
        config={},
    )
    
    cmd = MyCommand(app)
    exit_code = cmd.run()
    
    assert exit_code == 0


def test_command_dry_run():
    """Test command respects dry-run mode."""
    app = AppContext(
        project_root=Path.cwd(),
        config={},
        dry_run=True,
    )
    
    cmd = MyCommand(app)
    exit_code = cmd.run()
    
    # Should succeed without performing actual work
    assert exit_code == 0
```

## Example Use Cases

### Custom Build Command

```python
class CustomBuildCommand(Command):
    name = "custom-build"
    help = "Custom build process for this project"
    
    def run(self, **kwargs) -> int:
        self.app.logger.info("Running custom build")
        
        # Run custom build steps
        steps = [
            ["python", "generate_files.py"],
            ["python", "-m", "build"],
            ["python", "post_build.py"],
        ]
        
        for step in steps:
            if self.app.dry_run:
                self.app.logger.info(f"[DRY-RUN] Would run: {' '.join(step)}")
            else:
                # Actually run the command
                import subprocess
                result = subprocess.run(step, capture_output=True)
                if result.returncode != 0:
                    self.app.logger.error(f"Build step failed: {' '.join(step)}")
                    return result.returncode
        
        return 0
```

### Project-Specific Task

```python
class DeployCommand(Command):
    name = "deploy"
    help = "Deploy to production environment"
    
    def run(self, **kwargs) -> int:
        # Get deployment config from app context
        deploy_config = self.app.config.get('deploy', {})
        target = deploy_config.get('target', 'production')
        
        self.app.logger.info(f"Deploying to {target}")
        
        if self.app.dry_run:
            self.app.logger.info("[DRY-RUN] Would deploy artifacts")
            return 0
        
        # Actual deployment logic
        # ...
        
        return 0
```

## Troubleshooting

### Plugin Not Found

If your plugin isn't being discovered:

1. Check that the module is importable: `python -c "import mypackage.plugin"`
2. Verify config syntax in `pyproject.toml` or `devflow.toml`
3. Check for typos in entry point names
4. Run with verbose flag: `devflow -vv plugin-list`

### Plugin Fails to Load

Check the error message:

```bash
devflow -v plugin-list
```

Common issues:
- Missing `register` function
- Import errors in plugin code
- Syntax errors in plugin module

### Command Not Registered

If your command isn't showing up:

1. Verify `register` function is being called
2. Check command name is unique
3. Ensure `Command.name` matches what you're registering
4. Look for errors in plugin loading: `devflow -vv plugin-list`

## Additional Resources

- [Design Spec](DESIGN_SPEC.md) - Overall architecture and design
- [Development Plan](COPILOT_PLAN.md) - Implementation roadmap
- Sample Plugin: See `tests/fixtures/plugins/sample_plugin.py` in the devflow repository
