import base64
import typing
from typing import cast

from dishka import FromDishka
from faststream.nats import NatsRouter

from resume_service.domain.services.js import stream
from resume_service.infrastructure.adapters.file import FilesRepository
from resume_service.infrastructure.adapters.task import TaskAdapter
from resume_service.presentation.broker.models.file import FileId

if typing.TYPE_CHECKING:
    from io import BytesIO

inference_router = NatsRouter()


@inference_router.subscriber("inference.upload", stream=stream)
async def start_pipeline(
    file_id: FileId, repository: FromDishka[FilesRepository], service: FromDishka[TaskAdapter]
) -> str:
    """Run task pipeline."""
    file_info = await repository.get_file_by_id(file_id)

    file_content = cast("BytesIO", file_info.file)
    serializable_data = {
        "filename": file_info.file_name,
        "content": base64.b64encode(file_content).decode("ascii"),  # Convert bytes to base64 string
        "content_type": file_info.content_type,
        "file_id": file_id,
    }

    return await service.create_task(serializable_data)
