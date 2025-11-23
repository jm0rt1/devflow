# Simple Plugin Example

This example demonstrates how to create and use a custom devflow plugin.

## Files

- `my_plugin.py` - The plugin implementation
- `devflow.toml` - Configuration file that loads the plugin

## Usage

From this directory, run:

```bash
# Set PYTHONPATH so the plugin can be imported
export PYTHONPATH=.

# List available commands (should show 'greet' and 'info')
devflow plugin-list

# See registered commands
PYTHONPATH=. devflow plugin-list

# Use verbose logging to see plugin loading
PYTHONPATH=. devflow -v plugin-list

# Note: Command execution integration is part of Workstream B (Command Framework)
# This example demonstrates Workstream F: plugin registration and discovery.
```

## Plugin Structure

The plugin (`my_plugin.py`) implements:

1. **GreetCommand** - A simple greeting command
   - Supports `--name` argument
   - Respects `--dry-run` flag
   - Uses structured logging

2. **InfoCommand** - Display project information
   - Shows project root and configuration
   - Demonstrates accessing app context

3. **register()** - Entry point function
   - Registers commands with the registry
   - Called automatically by devflow

## Key Concepts

### Command Class

```python
class MyCommand(Command):
    name = "mycommand"  # Command name
    help = "Command description"  # Help text
    
    def run(self, **kwargs) -> int:
        # Command implementation
        return 0  # Exit code
```

### Register Function

```python
def register(registry: CommandRegistry, app: AppContext) -> None:
    registry.register(MyCommand.name, MyCommand)
```

### Accessing App Context

- `self.app.logger` - Structured logging
- `self.app.config` - Configuration dictionary
- `self.app.dry_run` - Dry-run mode flag
- `self.app.verbose` - Verbosity level
- `self.app.project_root` - Project root path

See [../../docs/PLUGIN_DEVELOPMENT.md](../../docs/PLUGIN_DEVELOPMENT.md) for complete documentation.
