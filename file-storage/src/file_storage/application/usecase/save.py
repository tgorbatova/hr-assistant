from typing import BinaryIO

from faststream.nats import NatsBroker

from file_storage.application.interfaces.usecase.file import SaveFileUseCase
from file_storage.application.models.file import SaveFileDto
from file_storage.domain.models.file import FileId, SaveFile
from file_storage.domain.repositories.file import FileRepository
from file_storage.domain.repositories.file_storage import SaveFileStorage
from file_storage.domain.repositories.js import stream
from file_storage.main.config import settings


class SaveFileInteractor(SaveFileUseCase):
    def __init__(self, repository: FileRepository, storage: SaveFileStorage, broker: NatsBroker) -> None:
        self._repository = repository
        self._storage = storage
        self.publisher = broker.publisher("inference.upload", stream=stream)

    async def save(self, file_info: SaveFileDto, file: BinaryIO) -> FileId:
        """Сохранение файла.

        :param file_info:
        :param file:
        """

        def _format_path(file_info: SaveFileDto) -> str:
            """Форматирование пути файла.

            :param file_info:
            :return:
            """
            return (
                f"{settings.INFRA.OBJECT_STORE.ROOT_PATH}/{file_info.folder}/{file_info.name}.{file_info.file_name.split('.')[-1]}"
                if file_info.folder
                else f"{settings.INFRA.OBJECT_STORE.ROOT_PATH}/{file_info.name}.{file_info.file_name.split('.')[-1]}"
            )

        save_file = SaveFile(
            id=file_info.id,
            file_name=file_info.file_name,
            name=file_info.name,
            folder_name=file_info.folder,
            size=file_info.size,
            file_path=_format_path(file_info),
        )
        file_id = await self._repository.save(save_file)

        await self._storage.store_file(file, _format_path(file_info), file_size=file_info.size)

        await self.publisher.publish(str(file_id))

        return file_id
