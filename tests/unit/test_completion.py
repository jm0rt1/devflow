"""Unit tests for shell completion generation."""

import pytest

from devflow.app import AppContext
from devflow.commands.completion import CompletionCommand


class TestCompletionCommand:
    """Test completion command functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.app = AppContext(verbosity=0, quiet=True)
        self.cmd = CompletionCommand(self.app)

    def test_bash_completion(self):
        """Test bash completion script generation."""
        # Capture stdout
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        
        exit_code = self.cmd.run(shell="bash")
        
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        
        assert exit_code == 0
        assert "# devflow bash completion script" in output
        assert "_devflow_completion()" in output
        assert "complete -F _devflow_completion devflow" in output
        assert "venv deps test build" in output

    def test_zsh_completion(self):
        """Test zsh completion script generation."""
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        
        exit_code = self.cmd.run(shell="zsh")
        
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        
        assert exit_code == 0
        assert "#compdef devflow" in output
        assert "_devflow()" in output
        assert "'venv:Manage project virtual environment'" in output
        assert "'completion:Generate shell completion script'" in output

    def test_fish_completion(self):
        """Test fish completion script generation."""
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        
        exit_code = self.cmd.run(shell="fish")
        
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        
        assert exit_code == 0
        assert "# devflow fish completion script" in output
        assert 'complete -c devflow' in output
        assert '"Manage project virtual environment"' in output
        assert '"Generate shell completion script"' in output

    def test_unsupported_shell(self):
        """Test handling of unsupported shell."""
        exit_code = self.cmd.run(shell="powershell")
        assert exit_code == 1

    def test_case_insensitive_shell(self):
        """Test that shell names are case-insensitive."""
        import io
        import sys
        captured = io.StringIO()
        sys.stdout = captured
        
        exit_code = self.cmd.run(shell="BASH")
        
        sys.stdout = sys.__stdout__
        output = captured.getvalue()
        
        assert exit_code == 0
        assert "_devflow_completion()" in output
