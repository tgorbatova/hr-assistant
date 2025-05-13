from asyncio import TaskGroup
from typing import BinaryIO, NamedTuple

import structlog.stdlib

from resume_service.domain.exceptions.files import GetFileError
from resume_service.domain.models.result import ResultType
from resume_service.domain.types.clients import FilesRequestClient
from resume_service.presentation.broker.models.file import FileId

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("files_gateway")


class FileInfo(NamedTuple):
    id: FileId
    name: str
    file_name: str
    path: str
    file: BinaryIO
    content_type: str


class FilesRepository:
    def __init__(self, client: FilesRequestClient) -> None:
        self._client = client

    async def get_file_by_id(self, file_id: FileId) -> FileInfo:
        """Получение файла по file_id.

        :return:
        """
        async with self._client as client, TaskGroup() as tg:
            file_task = tg.create_task(client.get(f"/{file_id}"))
            file_info_task = tg.create_task(client.get(f"/info/file/{file_id}"))
        file, file_info = file_task.result(), file_info_task.result()
        if file is None:
            _logger.error("Get file by id error, file_id=%s", file_id)
            msg = "Не удалось получить файл по id."
            raise GetFileError(msg)
        if file_info is None:
            _logger.error("Get file info by id error, file_id=%s", file_id)
            msg = "Не удалось получить информацию о файле по id."
            raise GetFileError(msg)

        result = FileInfo(
            id=file_id,
            name=file_info["metadata"]["name"],
            file_name=file_info["metadata"]["file_name"],
            path=file_info["metadata"]["path"],
            file=file,
            content_type= "application/octet-stream"
        )
        _logger.info("Returning file info, file_id=%s", file_id)
        return result

    async def save_result(self, type: ResultType, file_id: FileId, result: BinaryIO) -> None:
        raise NotImplementedError
