from abc import abstractmethod
from collections.abc import AsyncIterator
from typing import BinaryIO, Protocol

from file_storage.domain.models.file import SaveFolder


class SaveFileStorage(Protocol):
    @abstractmethod
    async def store_file(self, file: BinaryIO, file_path: str, file_size: int | str) -> None:
        """Сохранение файла в ObjectStore.

        :param file:
        :param file_path:
        :param file_size:
        """

    async def delete_folder(self, folder_name: str) -> None:
        """Delete all objects in a folder in S3-compatible storage."""

    async def delete_file(self, folder_name: str, file_name: str) -> None:
        """Delete object in S3-compatible storage."""

    async def list_files_in_folder(self, folder_name: str) -> list[str]:
        """List files in a folder in S3-compatible storage using a pre-signed URL."""

    async def list_folders_in_root(self) -> list[str]:
        """List files in a folder in S3-compatible storage using a pre-signed URL."""

    async def create_folder(self, folder_info: SaveFolder) -> None:
        """Create a folder in S3-compatible storage using a pre-signed URL."""


class FileStreamer(Protocol):
    @abstractmethod
    async def get_file_stream(self, file_name: str) -> AsyncIterator[bytes]:
        """Получение файла из ObjectStore.

        :param file_name
        """


class FileStorage(SaveFileStorage, FileStreamer, Protocol): ...
