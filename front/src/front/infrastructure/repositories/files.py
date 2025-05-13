from typing import BinaryIO, NamedTuple

import structlog.stdlib
from fastapi import UploadFile

from front.domain.exceptions.core import FrontError
from front.domain.models.file import File
from front.domain.types.clients import FilesRequestClient
from front.domain.types.file import FileId

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("files_gateway")


class FileInfo(NamedTuple):
    name: str
    data: BinaryIO
    mime_type: str


class FilesRepository:
    def __init__(self, client: FilesRequestClient) -> None:
        self._client = client

    async def get_all_folders(self) -> list[str]:
        """Получение всех папок (вакансий).

        :return: список папок
        """
        async with self._client as client:
            response = await client.get("/list/folders")
        if response is None:
            _logger.error("Get folders info error")
            msg = "Не удалось получить папки."
            raise FrontError(msg)

        return [folder.split("/")[-1] for folder in response]

    async def get_file_info(self, path: str) -> File:
        """Получение информации о файле (резюме) по пути.

        :return: File
        """
        async with self._client as client:
            response = await client.get("/info/file?path=%s" % path)
        if response is None:
            _logger.error("Get file info error")
            msg = "Не удалось получить информацию о файле."
            raise FrontError(msg)

        return response

    async def get_all_folder_files(self, folder: str) -> list[str]:
        """Получение всех файлов (резюме) в папке.

        :return: список файлов
        """
        async with self._client as client:
            response = await client.get("/list/files", params={"folder": folder})
        if response is None:
            _logger.error("Get folders info error")
            msg = "Не удалось получить папки."
            raise FrontError(msg)

        return [file.split("/")[-1] for file in response]

    async def upload_file_to_folder(self, folder: str, file: UploadFile):
        """Upload a file to the specified folder."""
        try:
            file.file.seek(0)
            async with self._client as client:
                await client.post(
                    f"/?folder={folder}",
                    files=file
                )
        except Exception as e:
            raise Exception(f"Failed to upload file: {e!s}")
