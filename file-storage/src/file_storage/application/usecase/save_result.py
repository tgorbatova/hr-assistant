from typing import BinaryIO

from file_storage.application.interfaces.usecase.file import SaveResultUseCase
from file_storage.application.models.result import SaveResultDto
from file_storage.domain.models.result import ResultId, ResultType, SaveResult
from file_storage.domain.repositories.file import FileRepository
from file_storage.domain.repositories.file_storage import SaveFileStorage
from file_storage.main.config import settings


class SaveResultInteractor(SaveResultUseCase):
    def __init__(self, repository: FileRepository, storage: SaveFileStorage) -> None:
        self._repository = repository
        self._storage = storage

    async def save(self, result_info: SaveResultDto, result: BinaryIO) -> ResultId:
        """Сохранение результата.

        :param result_info:
        :param result:
        """

        def _format_path(result_info: SaveResultDto) -> str:
            """Форматирование пути файла.

            :param result_info:
            :return:
            """
            match result_info.type:
                case ResultType.FORMAT:
                    return f"{settings.INFRA.OBJECT_STORE.RESULT_PATH}/{result_info.folder_name}/{result_info.file_name}/{result_info.type.value}/{result_info.file_name}_formatted.json"
                case ResultType.CONVERT:
                    return f"{settings.INFRA.OBJECT_STORE.RESULT_PATH}/{result_info.folder_name}/{result_info.file_name}/{result_info.type.value}/{result_info.file_name}_converted.txt"

        save_result = SaveResult(
            id=result_info.id,
            file_name=result_info.file_name,
            file_id=result_info.file_id,
            folder_name=result_info.folder_name,
            path=_format_path(result_info),
            type=result_info.type,
            size=result_info.size,
        )

        result_id = await self._repository.save_result(save_result)

        if result_info.type == ResultType.FORMAT:
            await self._repository.save_formatted_result(
                result_id,
                save_result.file_id,
                result,
                result_info.file_name,
            )

        await self._storage.store_file(result, _format_path(result_info), file_size=save_result.size)

        return result_id
