"""Git integration helpers for devflow."""

import re
import subprocess
from pathlib import Path
from typing import Optional


class GitError(Exception):
    """Base exception for git-related errors."""


class DirtyWorkingTreeError(GitError):
    """Raised when working tree is dirty and clean tree is required."""


def run_git_command(
    args: list[str],
    cwd: Optional[Path] = None,
    check: bool = True,
    capture_output: bool = True,
) -> subprocess.CompletedProcess:
    """
    Run a git command with explicit argument list (shell=False).

    Args:
        args: Git command arguments (e.g., ["status", "--porcelain"])
        cwd: Working directory for the command
        check: Whether to raise on non-zero exit
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess result

    Raises:
        GitError: If command fails and check=True
    """
    cmd = ["git"] + args
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=capture_output,
            text=True,
            check=check,
        )
        return result
    except subprocess.CalledProcessError as e:
        raise GitError(f"Git command failed: {' '.join(cmd)}\n{e.stderr}") from e
    except FileNotFoundError as e:
        raise GitError("Git executable not found. Is git installed?") from e


def is_git_repository(path: Optional[Path] = None) -> bool:
    """
    Check if the given path is inside a git repository.

    Args:
        path: Path to check (defaults to current directory)

    Returns:
        True if inside a git repository, False otherwise
    """
    try:
        run_git_command(
            ["rev-parse", "--git-dir"],
            cwd=path,
            check=True,
        )
        return True
    except GitError:
        return False


def is_working_tree_clean(path: Optional[Path] = None) -> bool:
    """
    Check if the git working tree is clean (no uncommitted changes).

    Args:
        path: Path to check (defaults to current directory)

    Returns:
        True if working tree is clean, False otherwise

    Raises:
        GitError: If not in a git repository or git command fails
    """
    result = run_git_command(
        ["status", "--porcelain"],
        cwd=path,
        check=True,
    )
    # If output is empty, working tree is clean
    return not result.stdout.strip()


def require_clean_working_tree(path: Optional[Path] = None, message: Optional[str] = None) -> None:
    """
    Ensure the working tree is clean, raise an error if not.

    Args:
        path: Path to check (defaults to current directory)
        message: Custom error message

    Raises:
        DirtyWorkingTreeError: If working tree is dirty
        GitError: If not in a git repository or git command fails
    """
    if not is_working_tree_clean(path):
        if message is None:
            message = (
                "Working tree not clean. Commit or stash your changes before proceeding.\n"
                "Use --allow-dirty to bypass this check."
            )
        raise DirtyWorkingTreeError(message)


def get_current_commit_hash(path: Optional[Path] = None, short: bool = False) -> str:
    """
    Get the current commit hash.

    Args:
        path: Path to check (defaults to current directory)
        short: Whether to return short hash

    Returns:
        Commit hash (full or short)

    Raises:
        GitError: If not in a git repository or git command fails
    """
    args = ["rev-parse"]
    if short:
        args.append("--short")
    args.append("HEAD")

    result = run_git_command(args, cwd=path, check=True)
    return result.stdout.strip()


def format_tag(version: str, tag_format: str = "v{version}", tag_prefix: str = "") -> str:
    """
    Format a version string into a git tag name.

    Args:
        version: Version string (e.g., "1.0.0")
        tag_format: Format string with {version} placeholder
        tag_prefix: Additional prefix to prepend

    Returns:
        Formatted tag name

    Examples:
        >>> format_tag("1.0.0", "v{version}")
        'v1.0.0'
        >>> format_tag("1.0.0", "release-{version}", "prod/")
        'prod/release-1.0.0'
    """
    # First apply the format
    tag = tag_format.format(version=version)
    # Then prepend the prefix if provided
    if tag_prefix:
        tag = tag_prefix + tag
    return tag


def tag_exists(tag_name: str, path: Optional[Path] = None) -> bool:
    """
    Check if a git tag exists.

    Args:
        tag_name: Name of the tag to check
        path: Path to check (defaults to current directory)

    Returns:
        True if tag exists, False otherwise

    Raises:
        GitError: If not in a git repository (other than tag not found)
    """
    try:
        run_git_command(
            ["rev-parse", "--verify", f"refs/tags/{tag_name}"],
            cwd=path,
            check=True,
        )
        return True
    except GitError:
        return False


def create_tag(
    tag_name: str,
    message: Optional[str] = None,
    path: Optional[Path] = None,
    force: bool = False,
    dry_run: bool = False,
) -> bool:
    """
    Create a git tag.

    Args:
        tag_name: Name of the tag to create
        message: Optional tag message (creates annotated tag if provided)
        path: Path to repository (defaults to current directory)
        force: Whether to force tag creation (overwrite existing)
        dry_run: If True, only log what would be done

    Returns:
        True if tag was created, False if it already existed (idempotent)

    Raises:
        GitError: If git command fails
    """
    # Check if tag already exists
    if tag_exists(tag_name, path) and not force:
        return False  # Idempotent: tag already exists

    if dry_run:
        action = "Would create" if not tag_exists(tag_name, path) else "Would overwrite"
        tag_type = "annotated" if message else "lightweight"
        print(f"[dry-run] {action} {tag_type} tag: {tag_name}")
        if message:
            print(f"[dry-run]   Message: {message}")
        return True

    # Build tag creation command
    args = ["tag"]
    if force:
        args.append("-f")
    if message:
        args.extend(["-a", "-m", message])
    args.append(tag_name)

    run_git_command(args, cwd=path, check=True)
    return True


def get_version_from_setuptools_scm(path: Optional[Path] = None) -> Optional[str]:
    """
    Get version using setuptools_scm.

    Args:
        path: Path to repository (defaults to current directory)

    Returns:
        Version string if successful, None otherwise
    """
    try:
        # Try to import and use setuptools_scm
        from setuptools_scm import get_version

        if path:
            version = get_version(root=str(path))
        else:
            version = get_version()
        return version
    except (ImportError, LookupError):
        # setuptools_scm not installed or not in a git repo
        return None


def get_version_from_git_tags(path: Optional[Path] = None) -> Optional[str]:
    """
    Get version from the most recent git tag.

    Args:
        path: Path to repository (defaults to current directory)

    Returns:
        Version string extracted from tag, or None if no tags found
    """
    try:
        result = run_git_command(
            ["describe", "--tags", "--abbrev=0"],
            cwd=path,
            check=True,
        )
        tag = result.stdout.strip()

        # Try to extract version from tag (e.g., "v1.0.0" -> "1.0.0")
        # Match common version patterns
        match = re.search(r'(\d+\.\d+\.\d+(?:[.-]\w+)?)', tag)
        if match:
            return match.group(1)
        return tag
    except GitError:
        return None


def get_current_version(
    path: Optional[Path] = None,
    version_source: str = "setuptools_scm",
    fallback_version: Optional[str] = None,
) -> str:
    """
    Get the current project version from various sources.

    Args:
        path: Path to repository (defaults to current directory)
        version_source: Source to use ("setuptools_scm", "git_tags", "config")
        fallback_version: Fallback version if all sources fail

    Returns:
        Version string

    Raises:
        ValueError: If version cannot be determined and no fallback provided
    """
    version = None

    if version_source == "setuptools_scm":
        version = get_version_from_setuptools_scm(path)
    elif version_source == "git_tags":
        version = get_version_from_git_tags(path)
    elif version_source == "config":
        # Use the provided fallback as the config source
        version = fallback_version
    else:
        # Try all sources in order
        version = (
            get_version_from_setuptools_scm(path)
            or get_version_from_git_tags(path)
            or fallback_version
        )

    if version is None:
        if fallback_version:
            return fallback_version
        raise ValueError(
            f"Could not determine version from source '{version_source}'. "
            "No git tags found and setuptools_scm not available."
        )

    return version
