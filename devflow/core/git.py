"""Git utilities for devflow."""

import subprocess
from pathlib import Path
from typing import Optional

from devflow.core.logging import DevFlowLogger


class GitManager:
    """
    Git operations manager.
    """

    def __init__(self, project_root: Path, logger: DevFlowLogger, dry_run: bool = False):
        """
        Initialize git manager.

        Args:
            project_root: Path to project root
            logger: Logger instance
            dry_run: If True, don't execute git commands
        """
        self.project_root = project_root
        self.logger = logger
        self.dry_run = dry_run

    def is_git_repo(self) -> bool:
        """Check if project root is a git repository."""
        git_dir = self.project_root / ".git"
        return git_dir.exists()

    def is_working_tree_clean(self) -> bool:
        """
        Check if the working tree is clean (no uncommitted changes).

        Returns:
            True if working tree is clean
        """
        if not self.is_git_repo():
            return True

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                check=True,
                shell=False,
            )
            # If output is empty, working tree is clean
            return len(result.stdout.strip()) == 0
        except subprocess.CalledProcessError:
            return False

    def tag_exists(self, tag: str) -> bool:
        """
        Check if a tag exists.

        Args:
            tag: Tag name

        Returns:
            True if tag exists
        """
        if not self.is_git_repo():
            return False

        try:
            subprocess.run(
                ["git", "rev-parse", tag],
                cwd=self.project_root,
                capture_output=True,
                check=True,
                shell=False,
            )
            return True
        except subprocess.CalledProcessError:
            return False

    def create_tag(self, tag: str, message: Optional[str] = None) -> bool:
        """
        Create a git tag.

        Args:
            tag: Tag name
            message: Optional tag message (creates annotated tag if provided)

        Returns:
            True if successful
        """
        if not self.is_git_repo():
            self.logger.warning("Not a git repository, skipping tag creation", phase="git")
            return False

        if self.tag_exists(tag):
            self.logger.warning(f"Tag {tag} already exists", phase="git")
            return False

        cmd = ["git", "tag"]
        if message:
            cmd.extend(["-a", tag, "-m", message])
        else:
            cmd.append(tag)

        self.logger.info(f"Creating tag: {tag}", phase="git")

        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would create tag: {tag}", phase="git")
            return True

        try:
            subprocess.run(
                cmd,
                cwd=self.project_root,
                check=True,
                shell=False,
            )
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to create tag: {e}", phase="git")
            return False

    def get_current_version(self) -> Optional[str]:
        """
        Try to get current version from git tags or setuptools_scm.

        Returns:
            Version string or None
        """
        if not self.is_git_repo():
            return None

        # Try to get version from git describe
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                cwd=self.project_root,
                capture_output=True,
                check=True,
                shell=False,
            )
            version = result.stdout.decode().strip()
            # Remove 'v' prefix if present
            if version.startswith("v"):
                version = version[1:]
            return version
        except subprocess.CalledProcessError:
            return None
