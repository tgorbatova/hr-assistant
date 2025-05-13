from abc import abstractmethod
from typing import Protocol

from file_storage.domain.models.file import File, FileId, Folder, FolderId, SaveFile, SaveFolder
from file_storage.domain.models.result import Result, ResultId, ResultType, SaveResult


class FileSaver(Protocol):
    @abstractmethod
    async def save(self, report: SaveFile) -> FileId:
        """Сохранение файла в базу данных."""

    @abstractmethod
    async def save_result(self, result_info: SaveResult) -> ResultId:
        """Сохранение результата в базу данных."""

    @abstractmethod
    async def create_folder(self, folder_info: SaveFolder) -> FolderId:
        """Сохранение папки в базу данных.

        :param folder_info:
        :return:
        """


class FileDeleter(Protocol):
    @abstractmethod
    async def delete(self, folder_name: str, file_name: str) -> None:
        """Удаление файла из базы данных."""

    @abstractmethod
    async def delete_folder(self, folder_info: Folder) -> None:
        """Удаление папки из базы данных.

        :param folder_info:
        :return:
        """


class FileGetter(Protocol):
    @abstractmethod
    async def get_file_by_id(self, file_id: FileId) -> File:
        """Получение файла по идентификатору.

        :param file_id:
        """

    async def get_file_info_by_path(self, path: str) -> File:
        """Получение информации о файле по пути.

        :param path:
        """

    @abstractmethod
    async def get_folder_info(self, folder_name: str) -> Folder:
        """Получение информации о папке по названию.

        :param folder_name:
        """

    async def get_result_by_file_id(self, file_id: FileId, type: ResultType) -> Result:
        """Получение результата по идентификатору файла.

        :param file_id:
        :param type:
        """


class FileRepository(FileSaver, FileDeleter, Protocol):
    """Репозиторий файлов."""


class FileReader(FileGetter, Protocol): ...
