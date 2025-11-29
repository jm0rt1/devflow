"""Tests for AppContext and application layer."""

import logging
from pathlib import Path

import pytest

from devflow.app import (
    VERBOSITY_DEBUG,
    VERBOSITY_DEFAULT,
    VERBOSITY_QUIET,
    VERBOSITY_VERBOSE,
    AppContext,
    setup_logging,
)
from devflow.config import DEFAULT_CONFIG


class TestSetupLogging:
    """Tests for logging setup."""

    def test_quiet_sets_warning_level(self) -> None:
        """Quiet mode should set WARNING level."""
        logger = setup_logging(VERBOSITY_QUIET)
        assert logger.level == logging.WARNING

    def test_default_sets_info_level(self) -> None:
        """Default verbosity should set INFO level."""
        logger = setup_logging(VERBOSITY_DEFAULT)
        assert logger.level == logging.INFO

    def test_verbose_sets_debug_level(self) -> None:
        """Verbose mode should set DEBUG level."""
        logger = setup_logging(VERBOSITY_VERBOSE)
        assert logger.level == logging.DEBUG

    def test_debug_sets_debug_level(self) -> None:
        """Debug mode should set DEBUG level."""
        logger = setup_logging(VERBOSITY_DEBUG)
        assert logger.level == logging.DEBUG

    def test_logger_has_handler(self) -> None:
        """Logger should have a stream handler."""
        logger = setup_logging(VERBOSITY_DEFAULT)
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)


class TestAppContext:
    """Tests for AppContext creation and methods."""

    def test_create_with_project_root(self, tmp_path: Path) -> None:
        """Should create context with explicit project root."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        ctx = AppContext.create(project_root=tmp_path)

        assert ctx.project_root == tmp_path
        assert ctx.config is not None
        assert ctx.logger is not None
        assert ctx.verbosity == VERBOSITY_DEFAULT
        assert ctx.dry_run is False

    def test_create_with_config_file(self, tmp_path: Path) -> None:
        """Should create context with config from file."""
        (tmp_path / "pyproject.toml").write_text("""
[tool.devflow]
venv_dir = ".custom-venv"
""")

        ctx = AppContext.create(project_root=tmp_path)

        assert ctx.config.venv_dir == ".custom-venv"

    def test_create_with_dry_run(self, tmp_path: Path) -> None:
        """Should set dry_run flag."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        ctx = AppContext.create(project_root=tmp_path, dry_run=True)

        assert ctx.dry_run is True

    def test_create_with_verbosity(self, tmp_path: Path) -> None:
        """Should set verbosity level."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        ctx = AppContext.create(project_root=tmp_path, verbosity=VERBOSITY_DEBUG)

        assert ctx.verbosity == VERBOSITY_DEBUG
        assert ctx.logger.level == logging.DEBUG

    def test_create_nonexistent_project_root_raises(self, tmp_path: Path) -> None:
        """Should raise when explicit project root doesn't exist."""
        nonexistent = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError):
            AppContext.create(project_root=nonexistent)

    def test_log_methods(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Should log messages with appropriate levels."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        ctx = AppContext.create(project_root=tmp_path, verbosity=VERBOSITY_DEBUG)

        with caplog.at_level(logging.DEBUG, logger="devflow"):
            ctx.log("Info message")
            ctx.debug("Debug message")
            ctx.warning("Warning message")
            ctx.error("Error message")

        assert "Info message" in caplog.text
        assert "Debug message" in caplog.text
        assert "Warning message" in caplog.text
        assert "Error message" in caplog.text

    def test_log_with_phase(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Should include phase prefix in log messages."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")
        ctx = AppContext.create(project_root=tmp_path, verbosity=VERBOSITY_DEBUG)

        with caplog.at_level(logging.DEBUG, logger="devflow"):
            ctx.log("Running tests", phase="test")
            ctx.debug("Test details", phase="test")

        assert "[test] Running tests" in caplog.text
        assert "[test] Test details" in caplog.text

    def test_fallback_to_current_dir_when_no_root_markers(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Should use current directory when no project root markers found."""
        # Create empty directory without markers
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with caplog.at_level(logging.WARNING, logger="devflow"):
            ctx = AppContext.create(project_root=empty_dir)

        # Should use the specified directory
        assert ctx.project_root == empty_dir


class TestAppContextDefaults:
    """Tests for default configuration in AppContext."""

    def test_uses_default_config_when_no_config_file(self, tmp_path: Path) -> None:
        """Should use default config when no config files exist."""
        (tmp_path / "pyproject.toml").write_text("[project]\n")

        ctx = AppContext.create(project_root=tmp_path)

        # Config should have default values
        assert ctx.config.venv_dir == DEFAULT_CONFIG.venv_dir
        assert ctx.config.default_python == DEFAULT_CONFIG.default_python
        assert ctx.config.test_runner == DEFAULT_CONFIG.test_runner
