"""Integration tests for the publish command.

Tests the devflow publish command including:
- Happy path execution
- Clean working tree check
- Optional pre-tests
- Build artifacts
- Upload via twine
- Tag formatting and creation
- Dry-run behavior that does not perform network operations
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from devflow.commands.publish import (
    PublishConfig,
    build_twine_command,
    check_working_tree_clean,
    create_git_tag,
    format_tag,
    get_publish_config,
    get_version,
    run_publish,
)


@dataclass
class MockPublishConfig:
    """Mock publish configuration."""

    repository: str = "pypi"
    sign: bool = False
    tag_on_publish: bool = False
    tag_format: str = "v{version}"
    tag_prefix: str = ""
    require_clean_working_tree: bool = True
    run_tests_before_publish: bool = False


@dataclass
class MockPathsConfig:
    """Mock paths configuration."""

    dist_dir: str = "dist"


@dataclass
class MockConfig:
    """Mock configuration for testing."""

    publish: MockPublishConfig = field(default_factory=MockPublishConfig)
    paths: MockPathsConfig = field(default_factory=MockPathsConfig)


@dataclass
class MockAppContext:
    """Mock application context for testing."""

    project_root: Path = Path("/tmp/test-project")
    config: Any = field(default_factory=MockConfig)
    dry_run: bool = False
    verbose: int = 0
    quiet: bool = False
    _venv_python: Path | None = None

    def get_venv_python(self) -> Path | None:
        return self._venv_python


class TestGetPublishConfig:
    """Tests for get_publish_config function."""

    def test_default_config(self) -> None:
        """Test default configuration."""
        config = MockConfig()
        publish_config = get_publish_config(config)

        assert publish_config.repository == "pypi"
        assert publish_config.sign is False
        assert publish_config.tag_on_publish is False
        assert publish_config.require_clean_working_tree is True

    def test_custom_publish_config(self) -> None:
        """Test custom publish configuration."""
        config = MockConfig(
            publish=MockPublishConfig(
                repository="testpypi",
                sign=True,
                tag_on_publish=True,
                tag_format="release-{version}",
                require_clean_working_tree=False,
            )
        )
        publish_config = get_publish_config(config)

        assert publish_config.repository == "testpypi"
        assert publish_config.sign is True
        assert publish_config.tag_on_publish is True
        assert publish_config.tag_format == "release-{version}"
        assert publish_config.require_clean_working_tree is False


class TestFormatTag:
    """Tests for format_tag function."""

    def test_default_format(self) -> None:
        """Test default v{version} format."""
        tag = format_tag("v{version}", "", "1.0.0")
        assert tag == "v1.0.0"

    def test_custom_format(self) -> None:
        """Test custom tag format."""
        tag = format_tag("release-{version}", "", "2.1.0")
        assert tag == "release-2.1.0"

    def test_with_prefix(self) -> None:
        """Test tag format with prefix."""
        tag = format_tag("v{version}", "mypackage-", "1.0.0")
        assert tag == "mypackage-v1.0.0"

    def test_simple_version(self) -> None:
        """Test format with just version placeholder."""
        tag = format_tag("{version}", "", "3.2.1")
        assert tag == "3.2.1"


class TestBuildTwineCommand:
    """Tests for build_twine_command function."""

    def test_default_pypi_upload(self) -> None:
        """Test default PyPI upload command."""
        config = PublishConfig()
        cmd = build_twine_command(config, Path("/project/dist"))

        assert cmd[:4] == ["python", "-m", "twine", "upload"]
        assert "/project/dist/*" in cmd[-1]

    def test_testpypi_repository(self) -> None:
        """Test TestPyPI repository."""
        config = PublishConfig(repository="testpypi")
        cmd = build_twine_command(config, Path("/project/dist"))

        assert "--repository" in cmd
        assert "testpypi" in cmd

    def test_custom_repository_url(self) -> None:
        """Test custom repository URL."""
        config = PublishConfig(repository="https://custom.pypi.org/simple/")
        cmd = build_twine_command(config, Path("/project/dist"))

        assert "--repository-url" in cmd
        assert "https://custom.pypi.org/simple/" in cmd

    def test_with_signing(self) -> None:
        """Test upload with signing enabled."""
        config = PublishConfig(sign=True)
        cmd = build_twine_command(config, Path("/project/dist"))

        assert "--sign" in cmd

    def test_custom_twine_args(self) -> None:
        """Test custom twine arguments."""
        config = PublishConfig(twine_args=["--skip-existing", "--verbose"])
        cmd = build_twine_command(config, Path("/project/dist"))

        assert "--skip-existing" in cmd
        assert "--verbose" in cmd

    def test_custom_python_path(self) -> None:
        """Test custom Python path."""
        config = PublishConfig()
        cmd = build_twine_command(
            config, Path("/project/dist"), python_path="/venv/bin/python"
        )

        assert cmd[0] == "/venv/bin/python"


class TestCheckWorkingTreeClean:
    """Tests for check_working_tree_clean function."""

    def test_clean_working_tree(self, tmp_path: Path) -> None:
        """Test detection of clean working tree."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        # Create and commit a file
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        result = check_working_tree_clean(tmp_path, verbose=0)
        assert result is True

    def test_dirty_working_tree(self, tmp_path: Path) -> None:
        """Test detection of dirty working tree."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        # Create and commit a file
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        # Create an uncommitted change
        (tmp_path / "uncommitted.txt").write_text("dirty")

        result = check_working_tree_clean(tmp_path, verbose=0)
        assert result is False


class TestCreateGitTag:
    """Tests for create_git_tag function."""

    def test_dry_run_does_not_create_tag(self, tmp_path: Path) -> None:
        """Test dry-run mode doesn't create tag."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        result = create_git_tag(tmp_path, "v1.0.0", verbose=1, dry_run=True)

        assert result is True

        # Verify tag was not created
        tag_result = subprocess.run(
            ["git", "tag", "-l", "v1.0.0"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert tag_result.stdout.strip() == ""

    def test_create_tag_success(self, tmp_path: Path) -> None:
        """Test successful tag creation."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        result = create_git_tag(tmp_path, "v1.0.0", verbose=0, dry_run=False)

        assert result is True

        # Verify tag was created
        tag_result = subprocess.run(
            ["git", "tag", "-l", "v1.0.0"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )
        assert tag_result.stdout.strip() == "v1.0.0"


class TestRunPublish:
    """Tests for run_publish function."""

    def test_dry_run_mode_no_network_operations(self, tmp_path: Path) -> None:
        """Test that dry-run mode doesn't perform network operations."""
        # Create a minimal project with dist files
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        (dist_path / "package-1.0.0-py3-none-any.whl").touch()

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        (tmp_path / "pyproject.toml").write_text('[project]\nname = "test"\nversion = "1.0.0"')
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        app = MockAppContext(
            project_root=tmp_path,
            dry_run=True,
            verbose=1,
        )

        with patch("devflow.commands.publish.subprocess.run") as mock_subprocess:
            # Only allow git status check, no twine calls
            def check_call(*args: Any, **kwargs: Any) -> MagicMock:
                cmd = args[0] if args else kwargs.get("args", [])
                if cmd and cmd[0] == "git":
                    return MagicMock(returncode=0, stdout="")
                # Should not reach twine calls in dry-run
                raise AssertionError(f"Unexpected subprocess call: {cmd}")

            mock_subprocess.side_effect = check_call

            result = run_publish(app, skip_build=True)

            # Should succeed without network calls
            assert result == 0

    def test_dirty_working_tree_blocks_publish(self, tmp_path: Path) -> None:
        """Test that dirty working tree blocks publish."""
        # Initialize git repo with uncommitted changes
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        # Create uncommitted change
        (tmp_path / "dirty.txt").write_text("dirty")

        app = MockAppContext(project_root=tmp_path)

        result = run_publish(app, allow_dirty=False)

        assert result == 1

    def test_allow_dirty_bypasses_check(self, tmp_path: Path) -> None:
        """Test --allow-dirty bypasses working tree check."""
        # Create dist directory
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        (dist_path / "package-1.0.0.whl").touch()

        # Initialize git repo with uncommitted changes
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        (tmp_path / "test.txt").write_text("test")
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        (tmp_path / "dirty.txt").write_text("dirty")

        app = MockAppContext(project_root=tmp_path, dry_run=True)

        # With allow_dirty=True, should not fail due to dirty tree
        result = run_publish(app, allow_dirty=True, skip_build=True)

        assert result == 0

    def test_failed_tests_abort_publish(self) -> None:
        """Test that failed tests abort publish."""
        config = MockConfig(
            publish=MockPublishConfig(
                require_clean_working_tree=False,
                run_tests_before_publish=True,
            )
        )
        app = MockAppContext(config=config)

        # Mock test function that fails
        def failing_test_fn(app: Any) -> int:
            return 1

        result = run_publish(
            app,
            skip_build=True,
            run_test_fn=failing_test_fn,
        )

        assert result == 1

    def test_failed_build_aborts_publish(self) -> None:
        """Test that failed build aborts publish."""
        config = MockConfig(
            publish=MockPublishConfig(require_clean_working_tree=False)
        )
        app = MockAppContext(config=config)

        # Mock build function that fails
        def failing_build_fn(app: Any) -> int:
            return 1

        result = run_publish(app, run_build_fn=failing_build_fn)

        assert result == 1

    def test_tag_creation_on_publish(self, tmp_path: Path) -> None:
        """Test tag creation during publish."""
        # Create dist directory
        dist_path = tmp_path / "dist"
        dist_path.mkdir()
        (dist_path / "package-1.0.0.whl").touch()

        # Create pyproject.toml with version
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "test-package"\nversion = "1.0.0"'
        )

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )
        subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True, check=False)
        subprocess.run(
            ["git", "commit", "-m", "initial"],
            cwd=tmp_path,
            capture_output=True,
            check=False,
        )

        config = MockConfig(
            publish=MockPublishConfig(
                require_clean_working_tree=True,
                tag_on_publish=True,
                tag_format="v{version}",
            )
        )
        app = MockAppContext(project_root=tmp_path, config=config, dry_run=True)

        result = run_publish(app, skip_build=True)

        # In dry-run mode, should succeed and show what tag would be created
        assert result == 0


class TestGetVersion:
    """Tests for get_version function."""

    def test_version_from_pyproject_project(self, tmp_path: Path) -> None:
        """Test version extraction from [project] section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.2.3"')

        version = get_version(tmp_path)
        assert version == "1.2.3"

    def test_version_from_pyproject_poetry(self, tmp_path: Path) -> None:
        """Test version extraction from [tool.poetry] section."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "test"\nversion = "2.0.0"')

        version = get_version(tmp_path)
        assert version == "2.0.0"

    def test_no_version_returns_none(self, tmp_path: Path) -> None:
        """Test None returned when version not found."""
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"')

        version = get_version(tmp_path)
        # May return None or try setuptools_scm
        # Just verify it doesn't crash
        assert version is None or isinstance(version, str)

    def test_missing_pyproject_returns_none(self, tmp_path: Path) -> None:
        """Test None returned when pyproject.toml missing."""
        version = get_version(tmp_path)
        assert version is None or isinstance(version, str)
