import asyncio
import uuid
from time import time

import structlog.stdlib
from taskiq import AsyncTaskiqTask

from resume_service.domain.models.result import TaskResultDict
from resume_service.presentation.worker.tasks import task
from resume_service.presentation.worker.worker_setup import CancellableListQueueBroker

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("tasks_adapter")


class ResultTimeoutError(Exception):
    def __init__(self, task_id: str, timeout: int) -> None:
        super().__init__(f"Task {task_id} was not aborted in {timeout} seconds")


class TaskNotFoundError(Exception):
    def __init__(self, task_id: uuid.UUID) -> None:
        super().__init__(f"Task {task_id} was not found in broker")


class TaskAdapter:
    _cancel_wait_time: int = 10

    def __init__(self, broker: CancellableListQueueBroker) -> None:
        self._broker = broker

    async def create_task(
        self,
        data: dict,
    ) -> str:
        """Создание задачи."""
        taskk = self._broker.register_task(task, "task")
        task_info = await taskk.kicker().with_task_id(str(uuid.uuid4())).kiq(payload=data)
        await _logger.adebug("Registered task %s", task_info.task_id, task_id=task_info.task_id)

        return task_info.task_id

    async def abort_task(self, task_id: uuid.UUID) -> None:
        """Отмена задачи."""
        await self._broker.cancel_task(task_id)
        await _logger.adebug(
            "Sent cancel event for task %s to broker, waiting until the end for %s seconds...",
            task_id,
            self._cancel_wait_time,
            task_id=task_id,
        )
        task = self._get_task(task_id)
        start_time = time()
        while not await task.is_ready():
            await asyncio.sleep(0.1)
            if 0 < self._cancel_wait_time < time() - start_time:
                raise ResultTimeoutError(str(task_id), self._cancel_wait_time) from None
        # make sure that all progress tasks finished
        await _logger.adebug(
            "Task %s is aborted successfully. Waiting for 3 sec to finish progress tasks.",
            task_id,
            task_id=task_id,
        )
        await asyncio.sleep(3)

    def _get_task(self, task_id: uuid.UUID) -> AsyncTaskiqTask:
        return AsyncTaskiqTask(task_id=str(task_id), result_backend=self._broker.result_backend)

    async def get_task_result(self, task_id: uuid.UUID) -> str:
        """Получение результата задачи."""
        taskk = self._get_task(task_id)

        if not task:
            raise TaskNotFoundError(task_id)

        result = await taskk.wait_result(with_logs=True)
        if result.is_err:
            raise result.error
        return result.return_value

    async def get_task_status(self, task_id: uuid.UUID) -> TaskResultDict:
        """Получение статуса задачи."""
        task_status = await self._broker.get_task_status(task_id)

        return TaskResultDict(
            task_id=str(task_id),
            status=task_status,
        )
