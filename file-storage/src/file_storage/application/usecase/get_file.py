from collections.abc import AsyncIterator

from file_storage.application.interfaces.usecase.file import GetFileByIdUseCase, GetResultByIdUseCase
from file_storage.domain.models.file import File, FileId
from file_storage.domain.models.result import ResultType
from file_storage.domain.repositories.file import FileReader
from file_storage.domain.repositories.file_storage import FileStreamer


class GetFileByIdInteractor(GetFileByIdUseCase, GetResultByIdUseCase):
    def __init__(self, repository: FileReader, file_streamer: FileStreamer) -> None:
        self._repository = repository
        self._streamer = file_streamer

    async def get_file_by_id(self, file_id: FileId) -> tuple[AsyncIterator[bytes], str]:
        """Получение файла по идентификатору.

        :param file_id:
        :return:
        """
        file = await self._repository.get_file_by_id(file_id)
        return await self._streamer.get_file_stream(file_name=file.metadata.path), file.metadata.file_name

    async def get_file_info_by_id(self, file_id: FileId) -> File:
        """Получение информации о файле по идентификатору.

        :param file_id:
        :return:
        """
        return await self._repository.get_file_by_id(file_id)

    async def get_file_info_by_path(self, path: str) -> File:
        """Получение информации о файле по пути.

        :param path:
        :return:
        """
        return await self._repository.get_file_info_by_path(path)

    async def get_result_by_file_id(self, file_id: FileId, type: ResultType) -> AsyncIterator[bytes]:
        """Получение результата по идентификатору файла.

        :param file_id:
        :param type:
        """
        result = await self._repository.get_result_by_file_id(file_id, type)
        return await self._streamer.get_file_stream(file_name=result.metadata.path)
