"""Tests for pipeline expansion and cycle detection."""

import pytest

from devflow.commands.custom import CycleError, TaskNotFoundError, expand_pipeline
from devflow.config import TaskConfig


def test_expand_simple_command_task():
    """Test expanding a simple command task."""
    tasks_config = {
        "test": TaskConfig(
            command="pytest",
            args=["-v"],
            use_venv=True,
        )
    }

    tasks = expand_pipeline("test", tasks_config)

    assert len(tasks) == 1
    assert tasks[0].name == "test"
    assert tasks[0].command == ["pytest", "-v"]
    assert tasks[0].use_venv is True


def test_expand_pipeline_task():
    """Test expanding a pipeline task."""
    tasks_config = {
        "ci-check": TaskConfig(pipeline=["format", "lint", "test"]),
        "format": TaskConfig(command="ruff", args=["format"]),
        "lint": TaskConfig(command="ruff", args=["check", "."]),
        "test": TaskConfig(command="pytest", args=["-v"]),
    }

    tasks = expand_pipeline("ci-check", tasks_config)

    assert len(tasks) == 3
    assert tasks[0].name == "format"
    assert tasks[0].command == ["ruff", "format"]
    assert tasks[1].name == "lint"
    assert tasks[1].command == ["ruff", "check", "."]
    assert tasks[2].name == "test"
    assert tasks[2].command == ["pytest", "-v"]


def test_expand_nested_pipeline():
    """Test expanding nested pipelines."""
    tasks_config = {
        "full-check": TaskConfig(pipeline=["quick-check", "slow-test"]),
        "quick-check": TaskConfig(pipeline=["format", "lint"]),
        "format": TaskConfig(command="ruff", args=["format"]),
        "lint": TaskConfig(command="ruff", args=["check"]),
        "slow-test": TaskConfig(command="pytest", args=["--slow"]),
    }

    tasks = expand_pipeline("full-check", tasks_config)

    assert len(tasks) == 3
    assert tasks[0].name == "format"
    assert tasks[1].name == "lint"
    assert tasks[2].name == "slow-test"


def test_expand_task_not_found():
    """Test that expanding non-existent task raises error."""
    tasks_config = {
        "test": TaskConfig(command="pytest"),
    }

    with pytest.raises(TaskNotFoundError) as exc_info:
        expand_pipeline("nonexistent", tasks_config)

    assert "nonexistent" in str(exc_info.value)
    assert "test" in str(exc_info.value)  # Should list available tasks


def test_expand_pipeline_with_missing_subtask():
    """Test that pipeline with missing subtask raises error."""
    tasks_config = {
        "ci-check": TaskConfig(pipeline=["format", "nonexistent"]),
        "format": TaskConfig(command="ruff", args=["format"]),
    }

    with pytest.raises(TaskNotFoundError) as exc_info:
        expand_pipeline("ci-check", tasks_config)

    assert "nonexistent" in str(exc_info.value)


def test_detect_direct_cycle():
    """Test detection of direct self-reference cycle."""
    tasks_config = {
        "recursive": TaskConfig(pipeline=["recursive"]),
    }

    with pytest.raises(CycleError) as exc_info:
        expand_pipeline("recursive", tasks_config)

    assert "Cycle detected" in str(exc_info.value)
    assert "recursive" in str(exc_info.value)


def test_detect_indirect_cycle():
    """Test detection of indirect cycle."""
    tasks_config = {
        "a": TaskConfig(pipeline=["b"]),
        "b": TaskConfig(pipeline=["c"]),
        "c": TaskConfig(pipeline=["a"]),
    }

    with pytest.raises(CycleError) as exc_info:
        expand_pipeline("a", tasks_config)

    assert "Cycle detected" in str(exc_info.value)
    # Should show the cycle path
    error_msg = str(exc_info.value)
    assert "a" in error_msg
    assert "b" in error_msg or "c" in error_msg


def test_detect_complex_cycle():
    """Test detection of cycle in complex pipeline."""
    tasks_config = {
        "full": TaskConfig(pipeline=["lint", "test"]),
        "lint": TaskConfig(pipeline=["format"]),
        "format": TaskConfig(command="ruff", args=["format"]),
        "test": TaskConfig(pipeline=["full"]),  # Creates cycle
    }

    with pytest.raises(CycleError) as exc_info:
        expand_pipeline("full", tasks_config)

    assert "Cycle detected" in str(exc_info.value)


def test_no_false_positive_cycle():
    """Test that diamond dependencies don't trigger false cycle detection."""
    tasks_config = {
        "all": TaskConfig(pipeline=["a", "b"]),
        "a": TaskConfig(pipeline=["common"]),
        "b": TaskConfig(pipeline=["common"]),
        "common": TaskConfig(command="echo", args=["common"]),
    }

    # This should work - diamond pattern is allowed
    tasks = expand_pipeline("all", tasks_config)

    # Common task should appear twice (once for each branch)
    assert len(tasks) == 2
    assert tasks[0].name == "common"
    assert tasks[1].name == "common"


def test_task_with_custom_env():
    """Test that custom environment is preserved during expansion."""
    tasks_config = {
        "test": TaskConfig(
            command="pytest",
            env={"PYTEST_VERBOSE": "1"},
        )
    }

    tasks = expand_pipeline("test", tasks_config)

    assert len(tasks) == 1
    assert tasks[0].env == {"PYTEST_VERBOSE": "1"}


def test_task_without_venv():
    """Test that use_venv setting is preserved."""
    tasks_config = {
        "system-command": TaskConfig(
            command="ls",
            use_venv=False,
        )
    }

    tasks = expand_pipeline("system-command", tasks_config)

    assert len(tasks) == 1
    assert tasks[0].use_venv is False


def test_task_with_neither_command_nor_pipeline():
    """Test that task without command or pipeline raises error."""
    tasks_config = {
        "invalid": TaskConfig(),  # No command or pipeline
    }

    with pytest.raises(ValueError) as exc_info:
        expand_pipeline("invalid", tasks_config)

    assert "command" in str(exc_info.value) or "pipeline" in str(exc_info.value)
