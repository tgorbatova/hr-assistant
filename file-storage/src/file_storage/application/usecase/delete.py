from asyncio import TaskGroup

from file_storage.application.interfaces.usecase.file import DeleteFileUseCase, DeleteFolderUseCase
from file_storage.domain.repositories.file import FileRepository
from file_storage.domain.repositories.file_storage import SaveFileStorage
from file_storage.infrastructure.sqlalchemy.repositories.file import FileReadRepository


class DeleteInteractor(DeleteFolderUseCase, DeleteFileUseCase):
    def __init__(
        self,
        repository: FileReadRepository,
        delete_repository: FileRepository,
        storage: SaveFileStorage,
    ) -> None:
        self._repository = repository
        self._delete_repository = delete_repository
        self._storage = storage

    async def delete_folder(self, folder_name: str) -> None:
        """Удаление папки и ее содержимого.

        :param folder_name:
        """
        folder_info = await self._repository.get_folder_info(folder_name=folder_name)

        async with TaskGroup() as tg:
            tg.create_task(self._storage.delete_folder(folder_name))
            tg.create_task(self._delete_repository.delete_folder(folder_info))

    async def delete(self, folder_name: str, file_name: str) -> None:
        """Удаление файла.

        :param folder_name:
        :param file_name:
        """
        async with TaskGroup() as tg:
            tg.create_task(self._storage.delete_file(folder_name, file_name))
            tg.create_task(self._delete_repository.delete(folder_name, file_name.rpartition(".")[0]))
