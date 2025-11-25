# Troubleshooting Guide

This guide addresses common issues when using `devflow` across different platforms.

## Platform Compatibility

`devflow` is designed to work consistently across:
- **macOS** (zsh, bash)
- **Linux** (bash, sh)
- **Windows** (Git Bash, WSL)

## Common Issues

### Project Root Detection

#### Issue: "Project root not found"

**Symptoms:**
```
Error: Project root not found. Could not locate pyproject.toml or devflow.toml.
```

**Solutions:**
1. Ensure you're in a directory containing `pyproject.toml` or `devflow.toml`, or a subdirectory thereof
2. Use `--project-root PATH` to explicitly specify the project root:
   ```bash
   devflow --project-root /path/to/project test
   ```
3. Create a minimal `pyproject.toml` or `devflow.toml` in your project root

---

### Virtual Environment Issues

#### Issue: "Python interpreter not found"

**Symptoms:**
```
Error: Could not find Python interpreter: python3.11
```

**Solutions:**

**macOS:**
```bash
# Install with Homebrew
brew install python@3.11

# Or use pyenv
pyenv install 3.11
pyenv global 3.11
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv
```

**Windows (Git Bash/WSL):**
```bash
# WSL (Ubuntu)
sudo apt install python3.11 python3.11-venv

# Or use Windows Python and ensure it's in PATH
```

#### Issue: "venv already exists"

**Symptoms:**
```
Error: Virtual environment already exists at .venv
```

**Solution:**
Use the `--recreate` flag to force recreation:
```bash
devflow venv init --recreate
```

#### Issue: "Permission denied" when creating venv

**Solutions:**
1. Check directory permissions
2. On Windows, run terminal as Administrator if needed
3. Avoid creating venvs in system directories

---

### Dependency Issues

#### Issue: "pip install failed"

**Symptoms:**
```
Error: Failed to install dependencies from requirements.txt
```

**Solutions:**
1. Ensure `requirements.txt` exists and is valid
2. Check for network connectivity
3. Verify pip is up to date:
   ```bash
   devflow venv init
   .venv/bin/pip install --upgrade pip
   ```

#### Issue: "Could not find requirements file"

**Solution:**
Specify the correct path in your configuration:
```toml
[tool.devflow.deps]
requirements = "requirements/base.txt"
dev_requirements = "requirements/dev.txt"
```

---

### Build Issues

#### Issue: "build module not found"

**Symptoms:**
```
Error: No module named 'build'
```

**Solution:**
Install build in your venv:
```bash
devflow deps sync  # Ensure build is in requirements
# Or manually:
.venv/bin/pip install build
```

#### Issue: "No pyproject.toml with build-system"

**Solution:**
Add a `[build-system]` section to your `pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"
```

---

### Publish Issues

#### Issue: "Working tree not clean"

**Symptoms:**
```
Error: Working tree not clean; commit or stash before publish.
```

**Solutions:**
1. Commit or stash your changes:
   ```bash
   git add .
   git commit -m "Prepare for release"
   ```
2. Use `--allow-dirty` to bypass (not recommended for releases):
   ```bash
   devflow publish --allow-dirty
   ```
3. Disable the check in config (not recommended):
   ```toml
   [tool.devflow.publish]
   require_clean_working_tree = false
   ```

#### Issue: "twine upload failed"

**Solutions:**
1. Verify your PyPI credentials:
   ```bash
   # Check ~/.pypirc or use environment variables
   export TWINE_USERNAME=__token__
   export TWINE_PASSWORD=pypi-your-token-here
   ```
2. Test with TestPyPI first:
   ```toml
   [tool.devflow.publish]
   repository = "testpypi"
   ```
3. Use `--dry-run` to verify the command:
   ```bash
   devflow publish --dry-run
   ```

---

### Shell Completion Issues

#### Issue: Completion not working

**Solutions:**

**Bash:**
```bash
# Add to ~/.bashrc
eval "$(devflow completion bash)"
# Then reload:
source ~/.bashrc
```

**Zsh:**
```bash
# Add to ~/.zshrc
eval "$(devflow completion zsh)"
# Then reload:
source ~/.zshrc
# Or if using Oh My Zsh, you may need:
autoload -Uz compinit && compinit
```

**Fish:**
```fish
# Add to ~/.config/fish/config.fish
devflow completion fish | source
```

#### Issue: "Command not found" after installation

**Solutions:**
1. Ensure devflow is installed in your PATH:
   ```bash
   which devflow
   pip show devflow
   ```
2. If using pipx:
   ```bash
   pipx ensurepath
   ```
3. Start a new terminal session

---

## Platform-Specific Notes

### macOS

- **Gatekeeper issues:** If macOS blocks execution, go to System Preferences → Security & Privacy and allow the application
- **Homebrew Python:** Use `python3` instead of `python` in config:
  ```toml
  default_python = "python3"
  ```
- **M1/M2 Macs:** Some packages may require Rosetta or arm64-specific builds

### Linux

- **System Python:** Avoid using system Python for venvs; install a user Python or use pyenv
- **Missing venv module:**
  ```bash
  sudo apt install python3-venv  # Debian/Ubuntu
  sudo dnf install python3-venv  # Fedora
  ```

### Windows (Git Bash)

- **Path separators:** devflow handles path separators automatically; avoid hardcoding `/` or `\` in config
- **Executable extension:** Use `python` not `python.exe` in config
- **Long paths:** Enable long paths in Windows if you encounter path length issues:
  ```powershell
  # Run as Administrator
  New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
  ```

### Windows (WSL)

- **File permissions:** WSL may have issues with Windows file permissions. Consider using the Linux filesystem (e.g., `~/projects/`) instead of `/mnt/c/`
- **Line endings:** Configure git to handle line endings:
  ```bash
  git config --global core.autocrlf input
  ```

---

## Debugging

### Enable Verbose Output

Use verbosity flags to see what's happening:

```bash
devflow -v test       # Verbose output
devflow -vv test      # Debug output (shows commands)
```

### Dry Run Mode

Preview what commands would run without executing:

```bash
devflow --dry-run publish
devflow --dry-run build
```

### Check Configuration

Verify your configuration is being loaded correctly:

```bash
devflow --verbose --dry-run test
```

This shows:
- Which config file is being used
- The resolved configuration values
- What commands would be executed

---

## Getting Help

If you encounter issues not covered here:

1. Check the [Design Specification](DESIGN_SPEC.md) for intended behavior
2. Use `devflow --help` or `devflow <command> --help` for usage information
3. Open an issue on GitHub with:
   - Your platform (macOS/Linux/Windows)
   - Shell (bash/zsh/fish/Git Bash)
   - Python version
   - Full error message
   - Relevant configuration
