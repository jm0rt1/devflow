"""Shell completion generation command."""

from devflow.commands.base import Command


BASH_COMPLETION = """# devflow bash completion script
# Source this file in your ~/.bashrc or run: eval "$(devflow completion bash)"

_devflow_completion() {
    local cur prev commands
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"
    
    # Top-level commands
    commands="venv deps test build publish git task ci-check completion --help --version --dry-run --verbose --quiet --config --project-root"
    
    if [ $COMP_CWORD -eq 1 ]; then
        COMPREPLY=( $(compgen -W "${commands}" -- ${cur}) )
        return 0
    fi
    
    case "${prev}" in
        completion)
            COMPREPLY=( $(compgen -W "bash zsh fish" -- ${cur}) )
            return 0
            ;;
        venv)
            COMPREPLY=( $(compgen -W "init --help" -- ${cur}) )
            return 0
            ;;
        deps)
            COMPREPLY=( $(compgen -W "sync freeze --help" -- ${cur}) )
            return 0
            ;;
        --config|--project-root)
            COMPREPLY=( $(compgen -f -- ${cur}) )
            return 0
            ;;
    esac
}

complete -F _devflow_completion devflow
"""

ZSH_COMPLETION = """#compdef devflow
# devflow zsh completion script
# Add this file to your fpath or run: eval "$(devflow completion zsh)"

_devflow() {
    local -a commands
    commands=(
        'venv:Manage project virtual environment'
        'deps:Manage dependencies (sync, freeze)'
        'test:Run tests'
        'build:Build distribution artifacts'
        'publish:Build and upload to package index'
        'git:Git-related helper commands'
        'task:Run custom tasks defined in config'
        'ci-check:Opinionated CI pipeline'
        'completion:Generate shell completion script'
    )
    
    local -a global_opts
    global_opts=(
        '--help[Show help message]'
        '--version[Show version]'
        '--dry-run[Show what would be done without executing]'
        '--verbose[Increase verbosity]'
        '-v[Increase verbosity]'
        '--quiet[Suppress output]'
        '-q[Suppress output]'
        '--config[Configuration file path]'
        '--project-root[Project root directory]'
    )
    
    if (( CURRENT == 2 )); then
        _describe 'command' commands
        _describe 'option' global_opts
    else
        case "$words[2]" in
            completion)
                local -a shells
                shells=('bash' 'zsh' 'fish')
                _describe 'shell' shells
                ;;
            venv)
                _describe 'subcommand' '(init:Create virtual environment)'
                ;;
            deps)
                _describe 'subcommand' '(sync:Sync dependencies freeze:Freeze dependencies)'
                ;;
        esac
    fi
}

_devflow "$@"
"""

FISH_COMPLETION = """# devflow fish completion script
# Place in ~/.config/fish/completions/devflow.fish or run: devflow completion fish > ~/.config/fish/completions/devflow.fish

# Top-level commands
complete -c devflow -f -n "__fish_use_subcommand" -a "venv" -d "Manage project virtual environment"
complete -c devflow -f -n "__fish_use_subcommand" -a "deps" -d "Manage dependencies (sync, freeze)"
complete -c devflow -f -n "__fish_use_subcommand" -a "test" -d "Run tests"
complete -c devflow -f -n "__fish_use_subcommand" -a "build" -d "Build distribution artifacts"
complete -c devflow -f -n "__fish_use_subcommand" -a "publish" -d "Build and upload to package index"
complete -c devflow -f -n "__fish_use_subcommand" -a "git" -d "Git-related helper commands"
complete -c devflow -f -n "__fish_use_subcommand" -a "task" -d "Run custom tasks defined in config"
complete -c devflow -f -n "__fish_use_subcommand" -a "ci-check" -d "Opinionated CI pipeline"
complete -c devflow -f -n "__fish_use_subcommand" -a "completion" -d "Generate shell completion script"

# Global options
complete -c devflow -l help -d "Show help message"
complete -c devflow -l version -d "Show version"
complete -c devflow -l dry-run -d "Show what would be done without executing"
complete -c devflow -l verbose -s v -d "Increase verbosity"
complete -c devflow -l quiet -s q -d "Suppress output"
complete -c devflow -l config -r -d "Configuration file path"
complete -c devflow -l project-root -r -d "Project root directory"

# Completion subcommands
complete -c devflow -f -n "__fish_seen_subcommand_from completion" -a "bash" -d "Generate bash completion"
complete -c devflow -f -n "__fish_seen_subcommand_from completion" -a "zsh" -d "Generate zsh completion"
complete -c devflow -f -n "__fish_seen_subcommand_from completion" -a "fish" -d "Generate fish completion"

# Venv subcommands
complete -c devflow -f -n "__fish_seen_subcommand_from venv" -a "init" -d "Create virtual environment"

# Deps subcommands
complete -c devflow -f -n "__fish_seen_subcommand_from deps" -a "sync" -d "Sync dependencies"
complete -c devflow -f -n "__fish_seen_subcommand_from deps" -a "freeze" -d "Freeze dependencies"
"""


class CompletionCommand(Command):
    """Generate shell completion scripts."""

    name = "completion"
    help = "Generate shell completion script"

    def run(self, shell: str) -> int:
        """
        Generate completion script for specified shell.
        
        Args:
            shell: Shell type (bash, zsh, or fish)
            
        Returns:
            Exit code
        """
        shell = shell.lower()
        
        if shell == "bash":
            print(BASH_COMPLETION)
            return 0
        elif shell == "zsh":
            print(ZSH_COMPLETION)
            return 0
        elif shell == "fish":
            print(FISH_COMPLETION)
            return 0
        else:
            self.app.logger.error(f"Unsupported shell: {shell}", phase="completion")
            self.app.logger.error("Supported shells: bash, zsh, fish", phase="completion")
            return 1
