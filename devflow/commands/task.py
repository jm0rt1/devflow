"""Custom task execution command."""

from devflow.commands.base import Command


class TaskCommand(Command):
    """Run custom tasks defined in config."""

    name = "task"
    help = "Run custom tasks defined in config"

    def run(self, task_name: str, **kwargs) -> int:
        """
        Execute a custom task.
        
        Args:
            task_name: Name of the task to execute
            **kwargs: Additional arguments
            
        Returns:
            Exit code
        """
        task = self.app.config.get_task(task_name)
        
        if task is None:
            self.app.logger.error(f"Task not found: {task_name}", phase="task")
            available = self.app.config.list_tasks()
            if available:
                self.app.logger.info(f"Available tasks: {', '.join(available)}", phase="task")
            return 1
        
        self.app.logger.info(f"Running task: {task_name}", phase="task")
        
        # Handle pipeline tasks
        if task.pipeline:
            self.app.logger.debug(f"Task is a pipeline: {task.pipeline}", phase="task")
            for step in task.pipeline:
                self.app.logger.info(f"Pipeline step: {step}", phase="task")
        elif task.command:
            self.app.logger.debug(f"Command: {task.command} {' '.join(task.args)}", phase="task")
        
        # Stub implementation
        return 0
