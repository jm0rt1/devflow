"""Build command implementation."""

import shutil

from devflow.app import AppContext
from devflow.core.paths import get_venv_python


def build_command(
    app: AppContext,
    clean: bool = True,
) -> int:
    """
    Build distribution artifacts using configured build backend.

    Args:
        app: Application context
        clean: If True, clean dist directory before building

    Returns:
        Exit code (0 for success)
    """
    phase = "build"

    # Check if venv exists
    if not app.venv_exists():
        app.logger.error(
            f"Virtual environment not found at {app.venv_dir}. "
            "Run 'devflow venv init' first.",
            phase=phase,
        )
        return 1

    # Clean dist directory if requested
    if clean and app.dist_dir.exists():
        app.logger.info(f"Cleaning {app.dist_dir}", phase=phase)
        if not app.dry_run:
            shutil.rmtree(app.dist_dir)

    # Get build backend from config
    build_backend = app.config.build_backend
    app.logger.info(f"Building with {build_backend}", phase=phase)

    # Get Python from venv
    venv_python = get_venv_python(app.venv_dir)

    # Build command based on backend
    if build_backend == "build":
        # Standard python -m build
        cmd = [str(venv_python), "-m", "build"]
    elif build_backend == "hatchling":
        cmd = [str(venv_python), "-m", "hatchling", "build"]
    elif build_backend == "poetry-build":
        cmd = [str(venv_python), "-m", "poetry", "build"]
    else:
        # Custom backend - assume it's a module
        cmd = [str(venv_python), "-m", build_backend]

    # Run build
    try:
        result = app.runner.run(cmd, phase=phase, check=False)

        if result.returncode == 0 and app.dist_dir.exists() and not app.dry_run:
            # Log built artifacts
                artifacts = list(app.dist_dir.glob("*"))
                if artifacts:
                    app.logger.info(
                        f"Built {len(artifacts)} artifact(s):",
                        phase=phase,
                    )
                    for artifact in artifacts:
                        app.logger.info(f"  - {artifact.name}", phase=phase)

        return result.returncode
    except Exception as e:
        app.logger.error(f"Build failed: {e}", phase=phase)
        return 1
