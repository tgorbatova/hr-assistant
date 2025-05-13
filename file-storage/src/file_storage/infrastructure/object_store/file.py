from collections.abc import AsyncIterator
from typing import BinaryIO, NewType

import structlog
from aiohttp import ClientResponseError, ClientSession
from botocore.client import BaseClient
from starlette import status

from file_storage.domain.exceptions.file import (
    DeleteFromStorageError,
    FileError,
    FileNotFoundError,
    ReadFromStorageError,
    SaveToStorageError,
)
from file_storage.domain.models.file import SaveFolder
from file_storage.domain.repositories.file_storage import FileStorage
from file_storage.main.config import settings

S3Session = NewType("S3Session", ClientSession)
BucketName = NewType("BucketName", str)
S3ChunkSize = NewType("S3ChunkSize", int)
_logger: structlog.stdlib.BoundLogger = structlog.get_logger("files.object_store")


class S3ReportRepository(FileStorage):
    def __init__(
        self,
        session: S3Session,
        bucket: BucketName,
        boto_client: BaseClient,
        chunk_size: S3ChunkSize = S3ChunkSize(1024 * 1024),
    ) -> None:
        self._session = session
        self._bucket = bucket
        self._boto_client = boto_client
        self._chunk_size = chunk_size

    async def create_folder(self, folder: SaveFolder) -> None:
        """Create a folder in S3-compatible storage using a pre-signed URL."""
        folder_key = settings.INFRA.OBJECT_STORE.ROOT_PATH + "/" + folder.name.rstrip("/") + "/"
        request_url = self._boto_client.generate_presigned_url(
            "put_object", {"Bucket": self._bucket, "Key": folder_key}
        )

        async with self._session.put(request_url, data=b"", headers={"Content-Length": "0"}) as response:
            try:
                response.raise_for_status()
            except ClientResponseError as exc:
                await _logger.aerror("Failed to create folder. Status code %s", response.status, exc=exc)
                raise SaveToStorageError(folder_key) from exc

    async def list_files_in_folder(self, folder_name: str) -> list[str]:
        """List files in a folder in S3-compatible storage using a pre-signed URL."""
        try:
            paginator = self._boto_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                Bucket=self._bucket, Prefix=settings.INFRA.OBJECT_STORE.ROOT_PATH + "/" + folder_name + "/"
            ):
                _logger.debug("Looking for files in %s", page)
                contents = page.get("Contents", [])
                return [obj["Key"] for obj in contents if not obj["Key"].endswith("/")]
        except Exception as exc:
            await _logger.aerror("Failed to list files in folder: %s", folder_name, exc=exc)
            raise ReadFromStorageError(folder_name) from exc
        return []

    async def delete_folder(self, folder_name: str) -> None:
        """Delete all objects in a folder in S3-compatible storage."""
        prefix = settings.INFRA.OBJECT_STORE.ROOT_PATH + "/" + folder_name.rstrip("/") + "/"

        try:
            paginator = self._boto_client.get_paginator("list_objects_v2")
            objects_to_delete = []

            for page in paginator.paginate(Bucket=self._bucket, Prefix=prefix):
                contents = page.get("Contents", [])
                for obj in contents:
                    objects_to_delete.append({"Key": obj["Key"]})  # noqa: PERF401

            if objects_to_delete:
                # S3 allows max 1000 objects per delete
                for i in range(0, len(objects_to_delete), 1000):
                    chunk = objects_to_delete[i : i + 1000]
                    response = self._boto_client.delete_objects(Bucket=self._bucket, Delete={"Objects": chunk})
                    deleted = response.get("Deleted", [])
                    _logger.debug("Deleted %d objects from folder %s", len(deleted), folder_name)
            else:
                _logger.info("No objects found to delete in folder: %s", folder_name)

        except Exception as exc:
            await _logger.aerror("Failed to delete folder: %s", folder_name, exc=exc)
            raise DeleteFromStorageError(folder_name) from exc

    async def delete_file(self, folder_name: str, file_name: str) -> None:
        """Delete a file from S3-compatible storage."""
        try:
            key = f"{settings.INFRA.OBJECT_STORE.ROOT_PATH}/{folder_name}/{file_name}"

            response = self._boto_client.delete_object(Bucket=self._bucket, Key=key)

            deleted = response.get("DeleteMarker", False)
            if deleted:
                _logger.debug("Deleted file %s", key)
            else:
                _logger.warning("File deletion attempted, but no DeleteMarker found for %s", key)

        except Exception as exc:
            await _logger.aerror("Failed to delete file: %s", key, exc=exc)
            raise DeleteFromStorageError(key) from exc

    async def list_folders_in_root(self) -> list[str]:
        """List folders.py in the root of S3-compatible storage."""
        try:
            paginator = self._boto_client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                Bucket=self._bucket,
                Delimiter="/",
                Prefix=settings.INFRA.OBJECT_STORE.ROOT_PATH + "/",
            ):
                common_prefixes = page.get("CommonPrefixes", [])
                return [prefix["Prefix"].rstrip("/") for prefix in common_prefixes]
        except Exception as exc:
            await _logger.aerror("Failed to list folders.py in root", exc=exc)
            file_path = "root"
            raise ReadFromStorageError(file_path) from exc
        return []

    async def get_file_stream(self, file_name: str) -> AsyncIterator[bytes]:
        """Получение объекта из Object Storage.

        :param file_name:
        :return:
        """
        request_url = self._boto_client.generate_presigned_url("get_object", {"Bucket": self._bucket, "Key": file_name})

        async def stream_file() -> AsyncIterator[bytes]:
            async with self._session.get(request_url) as response:
                yield str(response.status).encode()
                async for chunk in response.content.iter_chunked(self._chunk_size):
                    yield chunk

        stream = stream_file()
        if (response_status := int((await anext(stream)).decode())) >= status.HTTP_400_BAD_REQUEST:
            if response_status == status.HTTP_404_NOT_FOUND:
                raise FileNotFoundError(file_name)
            await _logger.aerror("Unable to get file from S3: %s", response_status)
            msg = f"Не удалось получить файл из облака (код ответа {response_status})"
            raise FileError(msg)
        return stream

    async def store_file(self, file: BinaryIO, file_path: str, file_size: int | str) -> None:
        """Сохранение объекта в Object Storage.

        :param file:
        :param file_path:
        :param file_size:
        """
        request_url = self._boto_client.generate_presigned_url("put_object", {"Bucket": self._bucket, "Key": file_path})

        async with self._session.put(request_url, data=file, headers={"Content-Length": str(file_size)}) as response:
            try:
                response.raise_for_status()
            except ClientResponseError as exc:
                await _logger.aerror("Failed to store file. Status code %s", response.status, exc=exc)
                raise SaveToStorageError(file_path) from exc
