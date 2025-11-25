"""Shell completion generation for devflow.

This module provides shell completion scripts for bash, zsh, and fish shells.
Completion enhances the user experience by providing tab completion for commands,
subcommands, and options.

Usage:
    eval "$(devflow completion bash)"
    eval "$(devflow completion zsh)"
    devflow completion fish | source

See docs/COMPLETION.md for detailed setup instructions.

Note:
    This module is owned by Workstream G (UX/docs). Other workstreams should
    import and use these functions rather than reimplementing completion logic.
"""

from devflow.completion.generator import (
    generate_bash_completion,
    generate_zsh_completion,
    generate_fish_completion,
    get_completion_script,
)

__all__ = [
    "generate_bash_completion",
    "generate_zsh_completion",
    "generate_fish_completion",
    "get_completion_script",
]
