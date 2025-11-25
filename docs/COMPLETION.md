# Shell Completion

`devflow` provides tab completion for bash, zsh, and fish shells to enhance productivity.

## Quick Setup

### Bash

Add to your `~/.bashrc`:

```bash
eval "$(devflow completion bash)"
```

Then reload:
```bash
source ~/.bashrc
```

### Zsh

Add to your `~/.zshrc`:

```bash
eval "$(devflow completion zsh)"
```

Then reload:
```bash
source ~/.zshrc
```

### Fish

Add to your `~/.config/fish/config.fish`:

```fish
devflow completion fish | source
```

Or install as a permanent completion file:

```fish
devflow completion fish > ~/.config/fish/completions/devflow.fish
```

---

## Permanent Installation

For better shell startup performance, you can save the completion script to a file instead of using `eval`.

### Bash (System-wide)

```bash
sudo devflow completion bash > /etc/bash_completion.d/devflow
```

### Bash (User-only)

```bash
mkdir -p ~/.local/share/bash-completion/completions
devflow completion bash > ~/.local/share/bash-completion/completions/devflow
```

### Zsh (with Oh My Zsh)

```bash
devflow completion zsh > ~/.oh-my-zsh/completions/_devflow
```

Then add to your `~/.zshrc`:
```bash
autoload -Uz compinit && compinit
```

### Zsh (without Oh My Zsh)

```bash
# Create completions directory if it doesn't exist
mkdir -p ~/.zsh/completions

# Save completion script
devflow completion zsh > ~/.zsh/completions/_devflow

# Add to ~/.zshrc (if not already present):
# fpath=(~/.zsh/completions $fpath)
# autoload -Uz compinit && compinit
```

### Fish

```fish
devflow completion fish > ~/.config/fish/completions/devflow.fish
```

---

## What Gets Completed

The completion system provides suggestions for:

### Commands and Subcommands

```bash
devflow <TAB>
# Shows: venv, deps, test, build, publish, task, ci-check, completion, version

devflow venv <TAB>
# Shows: init

devflow deps <TAB>
# Shows: sync, freeze
```

### Global Options

```bash
devflow --<TAB>
# Shows: --config, --project-root, --verbose, --quiet, --dry-run, --version, --help
```

### Command-Specific Options

```bash
devflow venv init --<TAB>
# Shows: --python, --recreate, --help

devflow publish --<TAB>
# Shows: --dry-run, --allow-dirty, --skip-tests, --repository, --help
```

### Custom Tasks

When you have custom tasks defined in your configuration, they'll also be completed:

```bash
devflow task <TAB>
# Shows your configured tasks: docs, lint, format, etc.
```

---

## Troubleshooting

### Completion Not Working

1. **Verify devflow is installed and in PATH:**
   ```bash
   which devflow
   devflow --version
   ```

2. **Verify completion script generation:**
   ```bash
   devflow completion bash  # Should output completion script
   ```

3. **Check shell startup file is sourced:**
   ```bash
   # Bash
   echo $BASH_COMPLETION_VERSINFO
   
   # Zsh
   echo $ZSH_VERSION
   ```

### Zsh: "command not found: compdef"

Run these commands:
```bash
autoload -Uz compinit
compinit
```

Or add them to your `~/.zshrc` before the completion eval line.

### Bash: Completion Only Works for Some Commands

Ensure bash-completion is installed:
```bash
# macOS
brew install bash-completion@2

# Ubuntu/Debian
sudo apt install bash-completion

# Fedora
sudo dnf install bash-completion
```

### Fish: Completions Not Updating

Clear the fish completion cache:
```fish
rm -rf ~/.cache/fish
```

### Slow Shell Startup

If `eval "$(devflow completion ...)"` makes your shell slow to start:

1. Save to a file instead (see Permanent Installation above)
2. Use lazy loading:

**Bash:**
```bash
# Add to ~/.bashrc
_devflow_completion_loader() {
    eval "$(devflow completion bash)"
    complete -p devflow &>/dev/null || return 1
}
complete -F _devflow_completion_loader devflow
```

**Zsh:**
```zsh
# Add to ~/.zshrc
devflow() {
    unfunction devflow
    eval "$(command devflow completion zsh)"
    command devflow "$@"
}
```

---

## How It Works

`devflow completion <shell>` generates a shell-specific completion script that integrates with each shell's native completion system:

- **Bash:** Uses `complete` and `compgen` builtins
- **Zsh:** Uses the `compsys` completion system with `_arguments`
- **Fish:** Uses Fish's built-in completion system

The generated scripts:
1. Define completion functions for devflow commands
2. Register these functions with the shell's completion system
3. Dynamically query devflow for available commands and options

---

## Advanced: Custom Task Completion

Custom tasks defined in your `devflow.toml` or `pyproject.toml` are automatically included in completions. The completion system reads your project configuration to discover available tasks.

Example configuration:
```toml
[tool.devflow.tasks.docs]
command = "sphinx-build"
args = ["-b", "html", "docs/source", "docs/build"]

[tool.devflow.tasks.lint]
command = "ruff"
args = ["check", "."]

[tool.devflow.tasks.typecheck]
command = "mypy"
args = ["src"]
```

With this configuration:
```bash
devflow task <TAB>
# Shows: docs, lint, typecheck
```

---

## See Also

- [QUICKSTART.md](QUICKSTART.md) - Getting started guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting
- [DESIGN_SPEC.md](DESIGN_SPEC.md) - Full design specification
