"""Tests for Task and Pipeline abstractions.

Ownership: Workstream B (task/registry)
"""


from devflow.commands.task import Pipeline, Task, is_pipeline, is_task


class TestTask:
    """Tests for the Task dataclass."""

    def test_task_creation_minimal(self):
        """Tasks can be created with minimal parameters."""
        task = Task(name="test", command="pytest")
        assert task.name == "test"
        assert task.command == "pytest"
        assert task.args == []
        assert task.use_venv is True
        assert task.env is None
        assert task.working_dir is None

    def test_task_creation_full(self):
        """Tasks can be created with all parameters."""
        task = Task(
            name="build",
            command="python",
            args=["-m", "build"],
            use_venv=False,
            env={"DEBUG": "1"},
            working_dir="src",
        )
        assert task.name == "build"
        assert task.command == "python"
        assert task.args == ["-m", "build"]
        assert task.use_venv is False
        assert task.env == {"DEBUG": "1"}
        assert task.working_dir == "src"

    def test_to_command_list_no_args(self):
        """to_command_list works with no args."""
        task = Task(name="test", command="pytest")
        assert task.to_command_list() == ["pytest"]

    def test_to_command_list_with_args(self):
        """to_command_list includes args."""
        task = Task(name="test", command="pytest", args=["-v", "--tb=short"])
        assert task.to_command_list() == ["pytest", "-v", "--tb=short"]

    def test_task_equality(self):
        """Tasks with same values are equal."""
        task1 = Task(name="test", command="pytest", args=["-v"])
        task2 = Task(name="test", command="pytest", args=["-v"])
        assert task1 == task2

    def test_task_inequality(self):
        """Tasks with different values are not equal."""
        task1 = Task(name="test", command="pytest", args=["-v"])
        task2 = Task(name="test", command="pytest", args=["-q"])
        assert task1 != task2


class TestPipeline:
    """Tests for the Pipeline dataclass."""

    def test_pipeline_creation_minimal(self):
        """Pipelines can be created with minimal parameters."""
        pipeline = Pipeline(name="ci")
        assert pipeline.name == "ci"
        assert pipeline.steps == []

    def test_pipeline_creation_with_string_steps(self):
        """Pipelines can have string references as steps."""
        pipeline = Pipeline(name="ci", steps=["lint", "test", "build"])
        assert pipeline.name == "ci"
        assert pipeline.steps == ["lint", "test", "build"]

    def test_pipeline_creation_with_task_steps(self):
        """Pipelines can have Task objects as steps."""
        task1 = Task(name="lint", command="ruff", args=["check", "."])
        task2 = Task(name="test", command="pytest")
        pipeline = Pipeline(name="ci", steps=[task1, task2])
        assert pipeline.name == "ci"
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0] == task1
        assert pipeline.steps[1] == task2

    def test_pipeline_creation_mixed_steps(self):
        """Pipelines can mix string references and Task objects."""
        task = Task(name="test", command="pytest")
        pipeline = Pipeline(name="ci", steps=["lint", task, "build"])
        assert len(pipeline.steps) == 3
        assert pipeline.steps[0] == "lint"
        assert pipeline.steps[1] == task
        assert pipeline.steps[2] == "build"


class TestTypeCheckers:
    """Tests for the is_pipeline and is_task functions."""

    def test_is_pipeline_true(self):
        """is_pipeline returns True for Pipeline instances."""
        pipeline = Pipeline(name="ci", steps=["test"])
        assert is_pipeline(pipeline) is True

    def test_is_pipeline_false(self):
        """is_pipeline returns False for Task instances."""
        task = Task(name="test", command="pytest")
        assert is_pipeline(task) is False

    def test_is_task_true(self):
        """is_task returns True for Task instances."""
        task = Task(name="test", command="pytest")
        assert is_task(task) is True

    def test_is_task_false(self):
        """is_task returns False for Pipeline instances."""
        pipeline = Pipeline(name="ci", steps=["test"])
        assert is_task(pipeline) is False
