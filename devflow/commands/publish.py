"""Publish command implementation."""

from typing import Optional

from devflow.app import AppContext
from devflow.commands.build import build_command
from devflow.commands.test import test_command
from devflow.core.git import GitManager
from devflow.core.paths import get_venv_executable


def publish_command(
    app: AppContext,
    repository: Optional[str] = None,
    skip_tests: bool = False,
    allow_dirty: bool = False,
    skip_existing: bool = False,
) -> int:
    """
    Build and publish package to package index.

    Steps:
    1. Check working tree is clean (unless --allow-dirty)
    2. Run tests (unless --skip-tests)
    3. Build package
    4. Upload to repository via twine
    5. Create git tag (if configured)

    Args:
        app: Application context
        repository: Optional repository name (default from config)
        skip_tests: If True, skip running tests
        allow_dirty: If True, allow dirty working tree
        skip_existing: If True, skip files that already exist on server

    Returns:
        Exit code (0 for success)
    """
    phase = "publish"

    # Check if venv exists
    if not app.venv_exists():
        app.logger.error(
            f"Virtual environment not found at {app.venv_dir}. "
            "Run 'devflow venv init' first.",
            phase=phase,
        )
        return 1

    # Get publish config
    publish_config = app.config.publish
    repository = repository or publish_config.repository

    # Initialize git manager
    git = GitManager(app.project_root, app.logger, app.dry_run)

    # Step 1: Check working tree
    if publish_config.require_clean_working_tree and not allow_dirty:
        if not git.is_working_tree_clean():
            app.logger.error(
                "Working tree not clean. Commit or stash changes before publishing, "
                "or use --allow-dirty to bypass this check.",
                phase=phase,
            )
            return 1
        app.logger.info("Working tree is clean", phase=phase)

    # Step 2: Run tests if configured
    if publish_config.run_tests_before_publish and not skip_tests:
        app.logger.info("Running tests before publish", phase=phase)
        test_result = test_command(app)
        if test_result != 0:
            app.logger.error("Tests failed, aborting publish", phase=phase)
            return test_result
        app.logger.info("Tests passed", phase=phase)

    # Step 3: Build package
    app.logger.info("Building package", phase=phase)
    build_result = build_command(app, clean=True)
    if build_result != 0:
        app.logger.error("Build failed, aborting publish", phase=phase)
        return build_result

    # Step 4: Upload to repository
    app.logger.info(f"Uploading to {repository}", phase=phase)

    # Get twine from venv
    twine_executable = get_venv_executable(app.venv_dir, "twine")
    if not twine_executable.exists():
        # Try python -m twine
        venv_python = get_venv_executable(app.venv_dir, "python")
        cmd = [str(venv_python), "-m", "twine", "upload"]
    else:
        cmd = [str(twine_executable), "upload"]

    # Add repository
    if repository != "pypi":
        cmd.extend(["--repository", repository])

    # Add skip-existing if requested
    if skip_existing or publish_config.skip_existing:
        cmd.append("--skip-existing")

    # Add dist files
    dist_files = f"{app.dist_dir}/*"
    cmd.append(dist_files)

    try:
        result = app.runner.run(cmd, phase=phase, check=False)
        if result.returncode != 0:
            app.logger.error("Upload failed", phase=phase)
            return result.returncode
        app.logger.info("Upload successful", phase=phase)
    except Exception as e:
        app.logger.error(f"Upload failed: {e}", phase=phase)
        return 1

    # Step 5: Create git tag if configured
    if publish_config.tag_on_publish:
        # Get version for tag
        version = git.get_current_version()
        if not version and app.dist_dir.exists():
            # Try to extract from built artifacts
                # Look for wheel or sdist
                for artifact in app.dist_dir.glob("*.whl"):
                    # Extract version from wheel name (package-version-...)
                    parts = artifact.stem.split("-")
                    if len(parts) >= 2:
                        version = parts[1]
                        break

                if not version:
                    for artifact in app.dist_dir.glob("*.tar.gz"):
                        # Extract version from sdist name (package-version.tar.gz)
                        stem = artifact.name.replace(".tar.gz", "")
                        parts = stem.split("-")
                        if len(parts) >= 2:
                            version = parts[1]
                            break

        if version:
            tag_name = publish_config.tag_format.format(version=version)
            git.create_tag(tag_name, message=f"Release {version}")
        else:
            app.logger.warning(
                "Could not determine version for tagging",
                phase=phase,
            )

    app.logger.info("Publish completed successfully", phase=phase)
    return 0
