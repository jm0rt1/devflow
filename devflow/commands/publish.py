"""Publish command implementation for devflow.

This module implements `devflow publish` pipeline respecting config flags:
- Require clean working tree (unless --allow-dirty)
- Optional pre-tests
- Build artifacts
- Upload via twine (repository configurable)
- Optional signing
- Tag creation following tag_format
- --dry-run to show would-be actions

Ownership: Workstream D
- Plugs into task engine and venv/git helpers
- Does not redefine config models, task execution, or git helpers
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from typing import Callable, Protocol

    class AppContextProtocol(Protocol):
        """Protocol for AppContext to avoid circular imports."""

        project_root: Path
        config: Any
        dry_run: bool
        verbose: int
        quiet: bool

        def get_venv_python(self) -> Path | None:
            """Get the python executable from the configured venv."""
            ...

    class GitHelperProtocol(Protocol):
        """Protocol for git helper functions from Workstream E."""

        def is_working_tree_clean(self, project_root: Path) -> bool:
            """Check if the git working tree is clean."""
            ...

        def create_tag(
            self, project_root: Path, tag: str, message: str | None = None
        ) -> bool:
            """Create a git tag."""
            ...

        def tag_exists(self, project_root: Path, tag: str) -> bool:
            """Check if a tag already exists."""
            ...


@dataclass
class PublishConfig:
    """Configuration for the publish command.

    Loaded from [tool.devflow.publish] and related sections in config.
    """

    repository: str = "pypi"  # "pypi", "testpypi", or custom URL
    sign: bool = False
    tag_on_publish: bool = False
    tag_format: str = "v{version}"
    tag_prefix: str = ""
    require_clean_working_tree: bool = True
    run_tests_before_publish: bool = False
    use_venv: bool = True
    env: dict[str, str] = field(default_factory=dict)
    dist_dir: str = "dist"
    twine_args: list[str] = field(default_factory=list)


def get_publish_config(config: Any) -> PublishConfig:
    """Extract publish configuration from the app config.

    Args:
        config: The loaded devflow configuration object.

    Returns:
        PublishConfig with appropriate settings.
    """
    # Get publish section
    publish = getattr(config, "publish", None)

    # Get paths for dist_dir
    paths = getattr(config, "paths", None)
    dist_dir = "dist"
    if paths:
        if isinstance(paths, dict):
            dist_dir = paths.get("dist_dir", "dist")
        else:
            dist_dir = getattr(paths, "dist_dir", "dist")

    if publish:
        if isinstance(publish, dict):
            return PublishConfig(
                repository=publish.get("repository", "pypi"),
                sign=publish.get("sign", False),
                tag_on_publish=publish.get("tag_on_publish", False),
                tag_format=publish.get("tag_format", "v{version}"),
                tag_prefix=publish.get("tag_prefix", ""),
                require_clean_working_tree=publish.get("require_clean_working_tree", True),
                run_tests_before_publish=publish.get("run_tests_before_publish", False),
                use_venv=publish.get("use_venv", True),
                env=publish.get("env", {}),
                dist_dir=publish.get("dist_dir", dist_dir),
                twine_args=publish.get("twine_args", []),
            )
        else:
            return PublishConfig(
                repository=getattr(publish, "repository", "pypi"),
                sign=getattr(publish, "sign", False),
                tag_on_publish=getattr(publish, "tag_on_publish", False),
                tag_format=getattr(publish, "tag_format", "v{version}"),
                tag_prefix=getattr(publish, "tag_prefix", ""),
                require_clean_working_tree=getattr(
                    publish, "require_clean_working_tree", True
                ),
                run_tests_before_publish=getattr(
                    publish, "run_tests_before_publish", False
                ),
                use_venv=getattr(publish, "use_venv", True),
                env=getattr(publish, "env", {}),
                dist_dir=getattr(publish, "dist_dir", dist_dir),
                twine_args=getattr(publish, "twine_args", []),
            )

    return PublishConfig(dist_dir=dist_dir)


def get_version(project_root: Path) -> str | None:
    """Get the project version.

    Attempts to determine version from various sources.
    This is a fallback - Workstream E's version helper should be preferred.

    Args:
        project_root: The project root directory.

    Returns:
        The version string, or None if not found.
    """
    # Try to get version from pyproject.toml
    pyproject_path = project_root / "pyproject.toml"
    if pyproject_path.exists():
        try:
            # Use tomllib (Python 3.11+) or tomli
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib

            with open(pyproject_path, "rb") as f:
                pyproject = tomllib.load(f)

            # Check [project] version
            if "project" in pyproject and "version" in pyproject["project"]:
                return pyproject["project"]["version"]

            # Check [tool.poetry] version
            if "tool" in pyproject:
                if "poetry" in pyproject["tool"]:
                    poetry = pyproject["tool"]["poetry"]
                    if "version" in poetry:
                        return poetry["version"]
        except Exception:
            pass

    # Try setuptools_scm
    try:
        from setuptools_scm import get_version as scm_get_version

        return scm_get_version(root=str(project_root))
    except Exception:
        pass

    return None


def format_tag(tag_format: str, tag_prefix: str, version: str) -> str:
    """Format a tag string using the configured format.

    Args:
        tag_format: The tag format string with {version} placeholder.
        tag_prefix: Optional prefix to prepend.
        version: The version string.

    Returns:
        The formatted tag string.
    """
    tag = tag_format.replace("{version}", version)
    if tag_prefix:
        tag = tag_prefix + tag
    return tag


def check_working_tree_clean(project_root: Path, verbose: int) -> bool:
    """Check if the git working tree is clean.

    Fallback implementation - Workstream E's git helper should be preferred.

    Args:
        project_root: The project root directory.
        verbose: Verbosity level.

    Returns:
        True if clean, False otherwise.
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        is_clean = result.returncode == 0 and not result.stdout.strip()
        if verbose > 0:
            if is_clean:
                print("[publish] Working tree is clean")
            else:
                print("[publish] Working tree has uncommitted changes")
        return is_clean
    except Exception as e:
        if verbose > 0:
            print(f"[publish] Could not check git status: {e}")
        return False


def create_git_tag(project_root: Path, tag: str, verbose: int, dry_run: bool) -> bool:
    """Create a git tag.

    Fallback implementation - Workstream E's git helper should be preferred.

    Args:
        project_root: The project root directory.
        tag: The tag name.
        verbose: Verbosity level.
        dry_run: If True, only log what would be done.

    Returns:
        True if successful, False otherwise.
    """
    if dry_run:
        print(f"[publish] Would create tag: {tag}")
        return True

    if verbose > 0:
        print(f"[publish] Creating tag: {tag}")

    try:
        result = subprocess.run(
            ["git", "tag", "-a", tag, "-m", f"Release {tag}"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            print(f"[publish] Failed to create tag: {result.stderr}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"[publish] Error creating tag: {e}", file=sys.stderr)
        return False


def build_twine_command(
    publish_config: PublishConfig,
    dist_path: Path,
    python_path: str = "python",
) -> list[str]:
    """Build the twine upload command.

    Args:
        publish_config: The publish configuration.
        dist_path: Path to the dist directory.
        python_path: Path to the Python executable.

    Returns:
        A list of command arguments for twine.
    """
    cmd = [python_path, "-m", "twine", "upload"]

    # Add repository
    if publish_config.repository == "testpypi":
        cmd.extend(["--repository", "testpypi"])
    elif publish_config.repository not in ("pypi", ""):
        # Custom repository URL
        cmd.extend(["--repository-url", publish_config.repository])

    # Add signing
    if publish_config.sign:
        cmd.append("--sign")

    # Add custom twine args
    cmd.extend(publish_config.twine_args)

    # Add dist files
    cmd.append(str(dist_path / "*"))

    return cmd


def run_publish(
    app: AppContextProtocol,
    allow_dirty: bool = False,
    skip_tests: bool = False,
    skip_build: bool = False,
    repository: str | None = None,
    extra_args: list[str] | None = None,
    run_test_fn: Callable[[AppContextProtocol], int] | None = None,
    run_build_fn: Callable[[AppContextProtocol], int] | None = None,
    git_helper: GitHelperProtocol | None = None,
) -> int:
    """Run the publish pipeline.

    Steps:
    1. Check working tree clean (unless --allow-dirty)
    2. Run tests (if configured and not skipped)
    3. Build artifacts (if not skipped)
    4. Upload via twine
    5. Create git tag (if configured)

    Args:
        app: The application context.
        allow_dirty: If True, allow publishing with uncommitted changes.
        skip_tests: If True, skip running tests before publish.
        skip_build: If True, skip building (use existing artifacts).
        repository: Override the configured repository.
        extra_args: Additional arguments to pass to twine.
        run_test_fn: Optional function to run tests (from test command).
        run_build_fn: Optional function to run build (from build command).
        git_helper: Optional git helper (from Workstream E).

    Returns:
        Exit code (0 for success, non-zero for failure).
    """
    publish_config = get_publish_config(app.config)

    # Override repository if specified
    if repository:
        publish_config.repository = repository

    # Step 1: Check working tree clean
    if publish_config.require_clean_working_tree and not allow_dirty:
        if git_helper:
            is_clean = git_helper.is_working_tree_clean(app.project_root)
        else:
            is_clean = check_working_tree_clean(app.project_root, app.verbose)

        if not is_clean:
            print(
                "[publish] Error: Working tree not clean; commit or stash before publish.",
                file=sys.stderr,
            )
            print(
                "[publish] Use --allow-dirty to publish anyway (not recommended).",
                file=sys.stderr,
            )
            return 1

    # Step 2: Run tests if configured
    if publish_config.run_tests_before_publish and not skip_tests:
        if app.verbose >= 0 and not app.quiet:
            print("[publish] Running tests before publish...")

        if app.dry_run:
            print("[publish] Would run tests")
        else:
            if run_test_fn:
                test_result = run_test_fn(app)
            else:
                # Fallback: import and run test command
                from devflow.commands.test import run_test

                test_result = run_test(app)

            if test_result != 0:
                print("[publish] Tests failed, aborting publish.", file=sys.stderr)
                return test_result

    # Step 3: Build artifacts
    if not skip_build:
        if app.verbose >= 0 and not app.quiet:
            print("[publish] Building artifacts...")

        if app.dry_run:
            print("[publish] Would build artifacts")
        else:
            if run_build_fn:
                build_result = run_build_fn(app)
            else:
                # Fallback: import and run build command
                from devflow.commands.build import run_build

                build_result = run_build(app)

            if build_result != 0:
                print("[publish] Build failed, aborting publish.", file=sys.stderr)
                return build_result

    # Step 4: Upload via twine
    dist_path = app.project_root / publish_config.dist_dir

    if not app.dry_run and not dist_path.exists():
        print(
            f"[publish] Error: Dist directory not found: {dist_path}",
            file=sys.stderr,
        )
        return 1

    # Determine Python path
    python_path = "python"
    if publish_config.use_venv:
        venv_python = app.get_venv_python()
        if venv_python and venv_python.exists():
            python_path = str(venv_python)

    cmd = build_twine_command(publish_config, dist_path, python_path)
    if extra_args:
        # Insert extra args before the file glob
        cmd = cmd[:-1] + extra_args + [cmd[-1]]

    cmd_str = " ".join(cmd)
    if app.verbose > 0:
        print(f"[publish] Running: {cmd_str}")

    if app.dry_run:
        print(f"[publish] Would upload to: {publish_config.repository}")
        print(f"[publish] Would run: {cmd_str}")
    else:
        # Build environment
        env = dict(publish_config.env) if publish_config.env else None

        try:
            # Note: twine upload needs special handling for the glob
            # We use shell=False but expand the glob manually
            import glob as glob_module

            dist_files = glob_module.glob(str(dist_path / "*"))
            if not dist_files:
                print(
                    f"[publish] Error: No files found in {dist_path}",
                    file=sys.stderr,
                )
                return 1

            # Replace glob with actual files
            actual_cmd = cmd[:-1] + dist_files

            result = subprocess.run(
                actual_cmd,
                cwd=app.project_root,
                env={**subprocess.os.environ, **env} if env else None,
                check=False,
            )

            if result.returncode != 0:
                print("[publish] Upload failed.", file=sys.stderr)
                return result.returncode

            if app.verbose >= 0 and not app.quiet:
                print(f"[publish] Successfully uploaded to {publish_config.repository}")

        except FileNotFoundError as e:
            print(f"[publish] Error: twine not found: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"[publish] Error during upload: {e}", file=sys.stderr)
            return 1

    # Step 5: Create git tag if configured
    if publish_config.tag_on_publish:
        version = get_version(app.project_root)
        if version:
            tag = format_tag(
                publish_config.tag_format,
                publish_config.tag_prefix,
                version,
            )

            if git_helper:
                if app.dry_run:
                    print(f"[publish] Would create tag: {tag}")
                elif git_helper.tag_exists(app.project_root, tag):
                    if app.verbose >= 0 and not app.quiet:
                        print(f"[publish] Tag already exists: {tag}")
                else:
                    if not git_helper.create_tag(app.project_root, tag):
                        print("[publish] Warning: Failed to create git tag", file=sys.stderr)
            else:
                if not create_git_tag(app.project_root, tag, app.verbose, app.dry_run):
                    if not app.dry_run:
                        print("[publish] Warning: Failed to create git tag", file=sys.stderr)

            if app.dry_run and app.verbose >= 0:
                print(f"[publish] Would create tag: {tag}")
        else:
            if app.verbose >= 0 and not app.quiet:
                print("[publish] Warning: Could not determine version for tagging")

    if app.verbose >= 0 and not app.quiet and not app.dry_run:
        print("[publish] Publish completed successfully!")

    return 0


# Typer command registration (if Typer is available)
def register_publish_command(app_typer: Any, get_app_context: Any) -> None:
    """Register the publish command with the Typer app.

    This function is called by the CLI module to register the publish command.

    Args:
        app_typer: The Typer application instance.
        get_app_context: A callable that returns the AppContext.
    """
    try:
        import typer
    except ImportError:
        return

    @app_typer.command()
    def publish(
        allow_dirty: bool = typer.Option(
            False,
            "--allow-dirty",
            help="Allow publishing with uncommitted changes",
        ),
        skip_tests: bool = typer.Option(
            False,
            "--skip-tests",
            help="Skip running tests before publish",
        ),
        skip_build: bool = typer.Option(
            False,
            "--skip-build",
            help="Skip building (use existing artifacts)",
        ),
        repository: str = typer.Option(
            None,
            "--repository",
            "-r",
            help="Repository to publish to (pypi, testpypi, or URL)",
        ),
        args: list[str] = typer.Argument(
            None,
            help="Additional arguments to pass to twine",
        ),
    ) -> None:
        """Build and publish package to PyPI or other repository.

        The publish pipeline:
        1. Checks working tree is clean (unless --allow-dirty)
        2. Optionally runs tests (if configured)
        3. Builds distribution artifacts
        4. Uploads via twine
        5. Creates git tag (if configured)

        Use --dry-run to see what would be done without making changes.

        Examples:
            devflow publish
            devflow publish --dry-run
            devflow publish --repository testpypi
            devflow publish --skip-tests --allow-dirty
        """
        ctx = get_app_context()
        exit_code = run_publish(
            ctx,
            allow_dirty=allow_dirty,
            skip_tests=skip_tests,
            skip_build=skip_build,
            repository=repository,
            extra_args=args,
        )
        raise typer.Exit(code=exit_code)
