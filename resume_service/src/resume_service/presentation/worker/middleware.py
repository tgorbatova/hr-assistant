import structlog
from redis.asyncio import ConnectionPool, Redis
from taskiq import TaskiqMessage, TaskiqMiddleware, TaskiqResult

from resume_service.domain.models.status import TaskStatus
from resume_service.infrastructure.context import task_id_var


class TaskStatusMiddleware(TaskiqMiddleware):
    """Middleware to handle task status updates."""

    def __init__(self, connection_pool: ConnectionPool) -> None:
        super().__init__()
        self.connection_pool = connection_pool

    logger: structlog.stdlib.BoundLogger = structlog.get_logger("middleware.logging")

    async def _set_task_status(self, task_id: str, status: TaskStatus) -> None:
        """Set the task status in Redis."""
        async with Redis(connection_pool=self.connection_pool) as redis_conn:
            await redis_conn.set(f"task_status:{task_id}", status.value)
            self.logger.debug("Set task %s status to %s", task_id, status.value)

    async def pre_send(self, message: TaskiqMessage) -> TaskiqMessage:
        """Set status to QUEUED when task is sent."""
        await self._set_task_status(message.task_id, TaskStatus.QUEUED)
        return message

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        """Set status to IN_PROGRESS when task starts."""
        task_id_var.set(message.task_id)
        await self._set_task_status(message.task_id, TaskStatus.IN_PROGRESS)
        return message

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult) -> None:
        """Set status based on task execution result."""
        if result.return_value is None:
            await self._set_task_status(message.task_id, TaskStatus.CANCELLED)
        else:
            await self._set_task_status(message.task_id, TaskStatus.COMPLETE)
