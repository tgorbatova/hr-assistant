import asyncio
import base64
import uuid
from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import inject
from fastapi import APIRouter, HTTPException, Query, UploadFile, status

from resume_service.infrastructure.adapters.task import TaskAdapter
from resume_service.presentation.api.models.create import CreateTaskQuery

router = APIRouter(prefix="/converter", tags=["converter"])


@router.post("/tasks", status_code=status.HTTP_202_ACCEPTED)
@inject
async def create_task(
    file: UploadFile, task_service: FromDishka[TaskAdapter], queries: Annotated[CreateTaskQuery, Query(...)]
) -> str:
    """Создание задачи."""
    file_content = await file.read()
    serializable_data = {
        "filename": file.filename,
        "content": base64.b64encode(file_content).decode("ascii"),  # Convert bytes to base64 string
        "content_type": file.content_type,
        "file_id": queries.file_id,
    }

    await file.seek(0)

    return await task_service.create_task(serializable_data)


@router.get("/{task_id}")
@inject
async def get_task(task_id: str, task_service: FromDishka[TaskAdapter]):
    """Получение информации о задаче."""
    try:
        result = await asyncio.wait_for(task_service.get_task_result(task_id=uuid.UUID(task_id)), timeout=30)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT, detail="Getting task result timeout. Please try again later."
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=next(iter(exc.args), "Error during task processing."),
        ) from exc
    return result


@router.get("/status/{task_id}")
@inject
async def get_task_status(task_id: str, task_service: FromDishka[TaskAdapter]):
    """Получение информации о задаче."""
    try:
        result = await task_service.get_task_status(task_id=uuid.UUID(task_id))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=next(iter(exc.args), "Error during getting task status."),
        ) from exc
    return result


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
@inject
async def delete_task(task_id: str, task_service: FromDishka[TaskAdapter]) -> None:
    """Отмена задачи."""
    await task_service.abort_task(task_id=uuid.UUID(task_id))
