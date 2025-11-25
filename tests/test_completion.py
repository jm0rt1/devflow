"""Tests for shell completion generation."""

from typing import List, cast

import pytest

from devflow.completion import (
    generate_bash_completion,
    generate_zsh_completion,
    generate_fish_completion,
    get_completion_script,
)
from devflow.completion.generator import ShellType

# Valid shell types for testing
VALID_SHELLS: List[ShellType] = ["bash", "zsh", "fish"]


class TestBashCompletion:
    """Tests for bash completion script generation."""

    def test_generates_non_empty_script(self):
        """Bash completion script should be non-empty."""
        script = generate_bash_completion()
        assert script
        assert len(script) > 100

    def test_contains_function_definition(self):
        """Bash completion script should define the completion function."""
        script = generate_bash_completion()
        assert "_devflow_completion()" in script

    def test_contains_complete_command(self):
        """Bash completion script should register with complete."""
        script = generate_bash_completion()
        assert "complete -F _devflow_completion devflow" in script

    def test_contains_all_main_commands(self):
        """Bash completion script should include all main commands."""
        script = generate_bash_completion()
        commands = ["venv", "deps", "test", "build", "publish", "task", "ci-check", "completion"]
        for cmd in commands:
            assert cmd in script, f"Command '{cmd}' not found in bash completion"

    def test_contains_global_options(self):
        """Bash completion script should include global options."""
        script = generate_bash_completion()
        options = ["--config", "--project-root", "--verbose", "--quiet", "--dry-run", "--version"]
        for opt in options:
            assert opt in script, f"Option '{opt}' not found in bash completion"


class TestZshCompletion:
    """Tests for zsh completion script generation."""

    def test_generates_non_empty_script(self):
        """Zsh completion script should be non-empty."""
        script = generate_zsh_completion()
        assert script
        assert len(script) > 100

    def test_contains_compdef_directive(self):
        """Zsh completion script should have compdef directive."""
        script = generate_zsh_completion()
        assert "#compdef devflow" in script

    def test_contains_main_function(self):
        """Zsh completion script should define the main function."""
        script = generate_zsh_completion()
        assert "_devflow()" in script

    def test_contains_commands_function(self):
        """Zsh completion script should define the commands function."""
        script = generate_zsh_completion()
        assert "_devflow_commands()" in script

    def test_contains_all_main_commands(self):
        """Zsh completion script should include all main commands."""
        script = generate_zsh_completion()
        commands = ["venv", "deps", "test", "build", "publish", "task", "ci-check", "completion"]
        for cmd in commands:
            assert cmd in script, f"Command '{cmd}' not found in zsh completion"

    def test_contains_command_descriptions(self):
        """Zsh completion script should include command descriptions."""
        script = generate_zsh_completion()
        descriptions = [
            "Manage project virtual environment",
            "Manage dependencies",
            "Run tests",
            "Build distribution",
        ]
        for desc in descriptions:
            assert desc in script, f"Description '{desc}' not found in zsh completion"


class TestFishCompletion:
    """Tests for fish completion script generation."""

    def test_generates_non_empty_script(self):
        """Fish completion script should be non-empty."""
        script = generate_fish_completion()
        assert script
        assert len(script) > 100

    def test_disables_default_file_completion(self):
        """Fish completion script should disable default file completion."""
        script = generate_fish_completion()
        assert "complete -c devflow -f" in script

    def test_contains_all_main_commands(self):
        """Fish completion script should include all main commands."""
        script = generate_fish_completion()
        commands = ["venv", "deps", "test", "build", "publish", "task", "ci-check", "completion"]
        for cmd in commands:
            assert cmd in script, f"Command '{cmd}' not found in fish completion"

    def test_contains_global_options(self):
        """Fish completion script should include global options."""
        script = generate_fish_completion()
        # Fish uses -l for long options, so we check for option names without dashes
        options = ["config", "project-root", "verbose", "quiet", "dry-run", "version"]
        for opt in options:
            assert opt in script, f"Option '{opt}' not found in fish completion"

    def test_contains_subcommand_completions(self):
        """Fish completion script should have subcommand-specific completions."""
        script = generate_fish_completion()
        # Check for venv subcommands
        assert "init" in script
        assert "__fish_seen_subcommand_from venv" in script
        # Check for deps subcommands
        assert "sync" in script
        assert "freeze" in script


class TestGetCompletionScript:
    """Tests for get_completion_script function."""

    def test_returns_bash_script(self):
        """Should return bash completion when requested."""
        script = get_completion_script("bash")
        assert "_devflow_completion()" in script
        assert "complete -F" in script

    def test_returns_zsh_script(self):
        """Should return zsh completion when requested."""
        script = get_completion_script("zsh")
        assert "#compdef devflow" in script
        assert "_devflow()" in script

    def test_returns_fish_script(self):
        """Should return fish completion when requested."""
        script = get_completion_script("fish")
        assert "complete -c devflow" in script

    def test_raises_for_unsupported_shell(self):
        """Should raise ValueError for unsupported shell."""
        with pytest.raises(ValueError) as exc_info:
            # Intentionally passing an invalid shell type to test error handling
            get_completion_script(cast(ShellType, "powershell"))
        assert "Unsupported shell" in str(exc_info.value)
        assert "powershell" in str(exc_info.value)

    def test_error_message_lists_supported_shells(self):
        """Error message should list supported shells."""
        with pytest.raises(ValueError) as exc_info:
            # Intentionally passing an invalid shell type to test error handling
            get_completion_script(cast(ShellType, "tcsh"))
        error_msg = str(exc_info.value)
        assert "bash" in error_msg
        assert "zsh" in error_msg
        assert "fish" in error_msg


class TestCompletionScriptSnapshots:
    """Snapshot tests for completion scripts.
    
    These tests verify that completion scripts maintain expected structure
    and content, helping catch unintended changes.
    """

    def test_bash_script_structure(self):
        """Bash script should have expected structure."""
        script = generate_bash_completion()
        lines = script.strip().split('\n')
        
        # Should start with comment header
        assert lines[0].startswith('#')
        assert 'bash completion' in lines[0].lower()
        
        # Should have function definition
        assert any('_devflow_completion()' in line for line in lines)
        
        # Should end with complete command
        assert 'complete -F _devflow_completion devflow' in lines[-1]

    def test_zsh_script_structure(self):
        """Zsh script should have expected structure."""
        script = generate_zsh_completion()
        lines = script.strip().split('\n')
        
        # Should start with compdef
        assert lines[0] == '#compdef devflow'
        
        # Should have main function
        assert any('_devflow()' in line for line in lines)
        
        # Should end with function call
        assert '_devflow "$@"' in lines[-1]

    def test_fish_script_structure(self):
        """Fish script should have expected structure."""
        script = generate_fish_completion()
        lines = script.strip().split('\n')
        
        # Should start with comment header
        assert lines[0].startswith('#')
        assert 'fish completion' in lines[0].lower()
        
        # Should disable file completion early
        assert any('complete -c devflow -f' in line for line in lines[:10])


class TestCompletionConsistency:
    """Tests ensuring consistency across all shell completions."""

    def test_all_shells_have_same_commands(self):
        """All shell completions should expose the same commands."""
        commands = ["venv", "deps", "test", "build", "publish", "task", "ci-check", "completion"]
        
        for shell in VALID_SHELLS:
            script = get_completion_script(shell)
            for cmd in commands:
                assert cmd in script, f"Command '{cmd}' missing in {shell} completion"

    def test_all_shells_have_venv_subcommands(self):
        """All shell completions should have venv subcommands."""
        for shell in VALID_SHELLS:
            script = get_completion_script(shell)
            assert "init" in script, f"'init' subcommand missing in {shell} completion"
            # Fish uses -l python, bash/zsh use --python
            assert "python" in script, f"'python' option missing in {shell} completion"
            assert "recreate" in script, f"'recreate' option missing in {shell} completion"

    def test_all_shells_have_deps_subcommands(self):
        """All shell completions should have deps subcommands."""
        for shell in VALID_SHELLS:
            script = get_completion_script(shell)
            assert "sync" in script, f"'sync' subcommand missing in {shell} completion"
            assert "freeze" in script, f"'freeze' subcommand missing in {shell} completion"

    def test_all_shells_have_publish_options(self):
        """All shell completions should have publish options."""
        # Use option names without dashes to support fish (which uses -l)
        publish_options = ["repository", "allow-dirty", "skip-tests"]
        
        for shell in VALID_SHELLS:
            script = get_completion_script(shell)
            for opt in publish_options:
                assert opt in script, f"'{opt}' option missing in {shell} completion"
