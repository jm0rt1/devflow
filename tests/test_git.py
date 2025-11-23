"""Tests for git integration helpers."""

import subprocess
from pathlib import Path

import pytest

from devflow.core.git import (
    DirtyWorkingTreeError,
    GitError,
    create_tag,
    format_tag,
    get_current_commit_hash,
    get_current_version,
    get_version_from_git_tags,
    is_git_repository,
    is_working_tree_clean,
    require_clean_working_tree,
    run_git_command,
    tag_exists,
)


class TestRunGitCommand:
    """Tests for run_git_command function."""

    def test_successful_command(self, temp_git_repo: Path) -> None:
        """Test running a successful git command."""
        result = run_git_command(["status", "--porcelain"], cwd=temp_git_repo)
        assert result.returncode == 0
        assert isinstance(result.stdout, str)

    def test_failed_command_with_check(self, temp_git_repo: Path) -> None:
        """Test that failed command raises GitError when check=True."""
        with pytest.raises(GitError, match="Git command failed"):
            run_git_command(["invalid-command"], cwd=temp_git_repo, check=True)

    def test_failed_command_without_check(self, temp_git_repo: Path) -> None:
        """Test that failed command doesn't raise when check=False."""
        result = run_git_command(
            ["invalid-command"], cwd=temp_git_repo, check=False, capture_output=True
        )
        assert result.returncode != 0


class TestIsGitRepository:
    """Tests for is_git_repository function."""

    def test_is_git_repository_true(self, temp_git_repo: Path) -> None:
        """Test that temp_git_repo is recognized as a git repository."""
        assert is_git_repository(temp_git_repo) is True

    def test_is_git_repository_false(self, tmp_path: Path) -> None:
        """Test that non-git directory is not recognized as a git repository."""
        non_git_dir = tmp_path / "not_a_repo"
        non_git_dir.mkdir()
        assert is_git_repository(non_git_dir) is False


class TestIsWorkingTreeClean:
    """Tests for is_working_tree_clean function."""

    def test_clean_working_tree(self, temp_git_repo: Path) -> None:
        """Test that clean repository is detected as clean."""
        assert is_working_tree_clean(temp_git_repo) is True

    def test_dirty_working_tree_with_new_file(self, dirty_git_repo: Path) -> None:
        """Test that repository with new file is detected as dirty."""
        assert is_working_tree_clean(dirty_git_repo) is False

    def test_dirty_working_tree_with_modified_file(self, temp_git_repo: Path) -> None:
        """Test that repository with modified file is detected as dirty."""
        readme = temp_git_repo / "README.md"
        readme.write_text("Modified content\n")
        assert is_working_tree_clean(temp_git_repo) is False

    def test_dirty_working_tree_with_staged_changes(self, temp_git_repo: Path) -> None:
        """Test that repository with staged changes is detected as dirty."""
        new_file = temp_git_repo / "staged.txt"
        new_file.write_text("Staged content\n")
        subprocess.run(
            ["git", "add", "staged.txt"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )
        assert is_working_tree_clean(temp_git_repo) is False


class TestRequireCleanWorkingTree:
    """Tests for require_clean_working_tree function."""

    def test_clean_tree_passes(self, temp_git_repo: Path) -> None:
        """Test that clean working tree doesn't raise."""
        require_clean_working_tree(temp_git_repo)  # Should not raise

    def test_dirty_tree_raises(self, dirty_git_repo: Path) -> None:
        """Test that dirty working tree raises DirtyWorkingTreeError."""
        with pytest.raises(DirtyWorkingTreeError, match="Working tree not clean"):
            require_clean_working_tree(dirty_git_repo)

    def test_custom_error_message(self, dirty_git_repo: Path) -> None:
        """Test that custom error message is used."""
        custom_msg = "Custom error message"
        with pytest.raises(DirtyWorkingTreeError, match=custom_msg):
            require_clean_working_tree(dirty_git_repo, message=custom_msg)


class TestGetCurrentCommitHash:
    """Tests for get_current_commit_hash function."""

    def test_get_full_hash(self, temp_git_repo: Path) -> None:
        """Test getting full commit hash."""
        hash_val = get_current_commit_hash(temp_git_repo)
        assert len(hash_val) == 40  # Full SHA-1 hash
        assert all(c in "0123456789abcdef" for c in hash_val)

    def test_get_short_hash(self, temp_git_repo: Path) -> None:
        """Test getting short commit hash."""
        hash_val = get_current_commit_hash(temp_git_repo, short=True)
        assert len(hash_val) >= 7  # Short hash is at least 7 characters
        assert len(hash_val) < 40  # But shorter than full hash
        assert all(c in "0123456789abcdef" for c in hash_val)


class TestFormatTag:
    """Tests for format_tag function."""

    def test_default_format(self) -> None:
        """Test default tag format (v{version})."""
        assert format_tag("1.0.0") == "v1.0.0"

    def test_custom_format(self) -> None:
        """Test custom tag format."""
        assert format_tag("1.0.0", tag_format="release-{version}") == "release-1.0.0"

    def test_with_prefix(self) -> None:
        """Test tag formatting with prefix."""
        assert format_tag("1.0.0", tag_format="v{version}", tag_prefix="prod/") == "prod/v1.0.0"

    def test_prefix_only(self) -> None:
        """Test tag formatting with prefix only."""
        assert format_tag("1.0.0", tag_format="{version}", tag_prefix="release/") == "release/1.0.0"

    def test_version_with_prerelease(self) -> None:
        """Test tag formatting with prerelease version."""
        assert format_tag("1.0.0-alpha.1") == "v1.0.0-alpha.1"


class TestTagExists:
    """Tests for tag_exists function."""

    def test_existing_tag(self, git_repo_with_tags: Path) -> None:
        """Test that existing tag is detected."""
        assert tag_exists("v1.0.0", git_repo_with_tags) is True

    def test_nonexistent_tag(self, git_repo_with_tags: Path) -> None:
        """Test that non-existent tag is not detected."""
        assert tag_exists("v2.0.0", git_repo_with_tags) is False

    def test_no_tags(self, temp_git_repo: Path) -> None:
        """Test tag_exists on repository with no tags."""
        assert tag_exists("v1.0.0", temp_git_repo) is False


class TestCreateTag:
    """Tests for create_tag function."""

    def test_create_lightweight_tag(self, temp_git_repo: Path) -> None:
        """Test creating a lightweight tag."""
        result = create_tag("v1.0.0", path=temp_git_repo)
        assert result is True
        assert tag_exists("v1.0.0", temp_git_repo)

    def test_create_annotated_tag(self, temp_git_repo: Path) -> None:
        """Test creating an annotated tag with message."""
        result = create_tag("v1.0.0", message="Release 1.0.0", path=temp_git_repo)
        assert result is True
        assert tag_exists("v1.0.0", temp_git_repo)

        # Verify tag message
        tag_info = run_git_command(
            ["tag", "-n1", "v1.0.0"],
            cwd=temp_git_repo,
        )
        assert "Release 1.0.0" in tag_info.stdout

    def test_idempotent_tag_creation(self, git_repo_with_tags: Path) -> None:
        """Test that creating existing tag returns False (idempotent)."""
        result = create_tag("v1.0.0", path=git_repo_with_tags)
        assert result is False  # Tag already exists
        assert tag_exists("v1.0.0", git_repo_with_tags)

    def test_force_tag_creation(self, git_repo_with_tags: Path) -> None:
        """Test forcing tag creation overwrites existing tag."""
        result = create_tag("v1.0.0", path=git_repo_with_tags, force=True)
        assert result is True
        assert tag_exists("v1.0.0", git_repo_with_tags)

    def test_dry_run_mode(self, temp_git_repo: Path, capsys) -> None:
        """Test that dry-run mode doesn't create tag."""
        result = create_tag("v1.0.0", path=temp_git_repo, dry_run=True)
        assert result is True  # Dry-run returns True
        assert not tag_exists("v1.0.0", temp_git_repo)  # But tag not actually created

        captured = capsys.readouterr()
        assert "[dry-run]" in captured.out
        assert "v1.0.0" in captured.out

    def test_dry_run_with_message(self, temp_git_repo: Path, capsys) -> None:
        """Test dry-run with annotated tag message."""
        result = create_tag(
            "v1.0.0",
            message="Test release",
            path=temp_git_repo,
            dry_run=True,
        )
        assert result is True
        assert not tag_exists("v1.0.0", temp_git_repo)

        captured = capsys.readouterr()
        assert "[dry-run]" in captured.out
        assert "annotated" in captured.out
        assert "Test release" in captured.out


class TestGetVersionFromGitTags:
    """Tests for get_version_from_git_tags function."""

    def test_get_version_from_latest_tag(self, git_repo_with_tags: Path) -> None:
        """Test getting version from latest git tag."""
        version = get_version_from_git_tags(git_repo_with_tags)
        assert version == "1.0.0"

    def test_no_tags_returns_none(self, temp_git_repo: Path) -> None:
        """Test that repository with no tags returns None."""
        version = get_version_from_git_tags(temp_git_repo)
        assert version is None

    def test_extract_version_from_prefixed_tag(self, temp_git_repo: Path) -> None:
        """Test extracting version from tag with prefix."""
        subprocess.run(
            ["git", "tag", "release-2.3.4"],
            cwd=temp_git_repo,
            check=True,
            capture_output=True,
        )
        version = get_version_from_git_tags(temp_git_repo)
        assert version == "2.3.4"


class TestGetCurrentVersion:
    """Tests for get_current_version function."""

    def test_fallback_version(self, temp_git_repo: Path) -> None:
        """Test using fallback version when no other source available."""
        version = get_current_version(
            temp_git_repo,
            version_source="config",
            fallback_version="0.1.0",
        )
        assert version == "0.1.0"

    def test_git_tags_source(self, git_repo_with_tags: Path) -> None:
        """Test getting version from git tags."""
        version = get_current_version(
            git_repo_with_tags,
            version_source="git_tags",
        )
        assert version == "1.0.0"

    def test_no_version_raises_error(self, temp_git_repo: Path) -> None:
        """Test that missing version without fallback raises error."""
        with pytest.raises(ValueError, match="Could not determine version"):
            get_current_version(temp_git_repo, version_source="git_tags")

    def test_fallback_when_git_tags_fail(self, temp_git_repo: Path) -> None:
        """Test using fallback when git tags are not available."""
        version = get_current_version(
            temp_git_repo,
            version_source="git_tags",
            fallback_version="0.2.0",
        )
        assert version == "0.2.0"
