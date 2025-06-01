from typing import BinaryIO, NamedTuple

import structlog.stdlib
from fastapi import UploadFile

from front.domain.exceptions.core import FrontError
from front.domain.models.file import File
from front.domain.types.clients import FilesRequestClient

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

    async def get_folder_files_filtered(self, folder: str, filters: str) -> list[str]:
        """Получение файлов (резюме) в папке, удовлетворяющих фильтрам.

        :return: список файлов
        """
        async with self._client as client:
            response = await client.get(f"/results/get/filtered?{filters}")
            _logger.debug("Got response: %s", response)
        if response is None:
            _logger.error("Get folders info error")
            msg = "Не удалось получить папки."
            raise FrontError(msg)

        file_ids = [r["file_id"] for r in response["items"]]

        file_names = []

        for i in file_ids:
            async with self._client as client:
                file_info = await client.get(f"/info/file/{i}")
                _logger.debug("Got file_info: %s", file_info)
            if file_info["metadata"]["folder_name"] == folder:
                file_names.append(file_info["metadata"]["path"].split("/")[-1])

        return file_names

    async def get_results_by_folder(self, folder: str) -> dict:
        async with self._client as client:
            response = await client.get("/results/get/filtered")
            _logger.debug("Got response: %s", response)
        if response is None:
            _logger.error("Get folders info error")
            msg = "Не удалось получить папки."
            raise FrontError(msg)

        file_ids = [r["file_id"] for r in response["items"]]

        items = []

        for i in file_ids:
            async with self._client as client:
                file_info = await client.get(f"/info/file/{i}")
                _logger.debug("Got file_info: %s", file_info)
            if file_info["metadata"]["folder_name"] == folder:
                items.append([res for res in response["items"] if res["file_id"] == i])

        response["items"] = items
        return response

    async def upload_file_to_folder(self, folder: str, file: UploadFile):
        """Upload a file to the specified folder."""
        try:
            file.file.seek(0)
            async with self._client as client:
                await client.post(f"/?folder={folder}", files=file)
        except Exception as e:
            raise Exception(f"Failed to upload file: {e!s}")
