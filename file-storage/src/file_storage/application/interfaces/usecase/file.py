from abc import abstractmethod
from asyncio import Protocol
from collections.abc import AsyncIterator
from typing import BinaryIO

from file_storage.application.models.file import SaveFileDto, SaveFolderDto
from file_storage.application.models.result import SaveResultDto
from file_storage.domain.models.file import File, FileId, Folder, FolderId
from file_storage.domain.models.result import ResultId, ResultType


class SaveFileUseCase(Protocol):
    @abstractmethod
    async def save(self, file_info: SaveFileDto, file: BinaryIO) -> FileId:
        """Сохранение файла.

        :param file_info:
        :param file:
        """


class SaveResultUseCase(Protocol):
    @abstractmethod
    async def save(self, result_info: SaveResultDto, result: BinaryIO) -> ResultId:
        """Сохранение результата.

        :param result_info:
        :param result:
        """


class DeleteFileUseCase(Protocol):
    @abstractmethod
    async def delete(self, folder_name: str, file_name: str) -> None:
        """Сохранение файла.

        :param folder_name:
        :param file_name:
        """


class CreateFolderUseCase(Protocol):
    @abstractmethod
    async def create_folder(self, folder_info: SaveFolderDto) -> FolderId:
        """Создание папки.

        :param folder_info:
        """


class DeleteFolderUseCase(Protocol):
    @abstractmethod
    async def delete_folder(self, folder_name: str) -> None:
        """Удаление папки и ее содержимого.

        :param folder_name:
        """


class GetInfoUseCase(Protocol):
    @abstractmethod
    async def get_folder_info(self, folder_name: str) -> Folder:
        """Получение информации о папке.

        :param folder_name:
        """


class GetResultByIdUseCase(Protocol):
    @abstractmethod
    async def get_result_by_file_id(self, file_id: FileId, type: ResultType) -> AsyncIterator[bytes]:
        """Получение результата по идентификатору файла.

        :param file_id:
        :param type:
        """


class GetFileByIdUseCase(Protocol):
    @abstractmethod
    async def get_file_by_id(self, file_id: FileId) -> AsyncIterator[bytes]:
        """Получение файла по идентификатору.

        :param file_id:
        """

    @abstractmethod
    async def get_file_info_by_id(self, file_id: FileId) -> File:
        """Получение информации о файле по идентификатору.

        :param file_id:
        """

    @abstractmethod
    async def get_file_info_by_path(self, path: str) -> File:
        """Получение информации о файле по пути.

        :param path:
        """


class ListFilesUseCase(Protocol):
    @abstractmethod
    async def list_files_in_folder(self, folder_name: str) -> list[str]:
        """Получение файлов в папке.

        :param folder_name:
        """


class ListFoldersUseCase(Protocol):
    @abstractmethod
    async def list_folders_in_root(self) -> list[str]:
        """Получение папок в руте."""
