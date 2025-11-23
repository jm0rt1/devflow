"""Tests for AppContext."""

import logging
import tempfile
from pathlib import Path

from devflow.app import AppContext
from devflow.config import DevflowConfig


def test_app_context_create_with_defaults():
    """Test creating AppContext with defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").touch()

        ctx = AppContext.create(project_root=root)

        assert ctx.project_root == root
        assert isinstance(ctx.config, DevflowConfig)
        assert ctx.verbose == 0
        assert ctx.quiet is False
        assert ctx.dry_run is False
        assert isinstance(ctx.logger, logging.Logger)


def test_app_context_with_verbose():
    """Test AppContext with verbose flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").touch()

        ctx = AppContext.create(project_root=root, verbose=2)

        assert ctx.verbose == 2
        assert ctx.logger.level == logging.DEBUG


def test_app_context_with_quiet():
    """Test AppContext with quiet flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").touch()

        ctx = AppContext.create(project_root=root, quiet=True)

        assert ctx.quiet is True
        assert ctx.logger.level == logging.ERROR


def test_app_context_with_dry_run():
    """Test AppContext with dry_run flag."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "pyproject.toml").touch()

        ctx = AppContext.create(project_root=root, dry_run=True)

        assert ctx.dry_run is True


def test_app_context_loads_config():
    """Test that AppContext loads configuration from project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create pyproject.toml with config
        pyproject = root / "pyproject.toml"
        pyproject.write_text(
            """
[tool.devflow]
venv_dir = ".custom-venv"
default_python = "python3.9"
"""
        )

        ctx = AppContext.create(project_root=root)

        assert ctx.config.venv_dir == ".custom-venv"
        assert ctx.config.default_python == "python3.9"
