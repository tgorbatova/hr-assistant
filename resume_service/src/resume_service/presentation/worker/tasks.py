import base64
from typing import Annotated

import structlog
from dishka import FromDishka
from dishka.integrations.taskiq import inject
from taskiq import AsyncBroker, Context, TaskiqDepends

from resume_service.app.interfaces.inference import Inference
from resume_service.domain.models.resume_info import ResumeInfo

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("tasks")


@inject
async def task(
    ctx: Annotated[Context, TaskiqDepends()],
    payload: dict,
    inference: FromDishka[Inference],
) -> ResumeInfo:
    """Convert input file to plain text."""
    _logger.debug("Preparing task %s execution", ctx.message.task_id)

    filename = payload["filename"]
    content = base64.b64decode(payload["content"])
    content_type = payload["content_type"]
    file_id = payload["file_id"]

    file_data = {"filename": filename, "content": content, "content_type": content_type, "file_id": file_id}

    return await inference.inference(file_data=file_data)


def register_tasks(broker: AsyncBroker) -> None:
    """Register tasks."""
    broker.register_task(task, task_name="task")
