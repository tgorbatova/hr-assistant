from file_storage.application.interfaces.usecase.file import ListFilesUseCase, ListFoldersUseCase
from file_storage.domain.repositories.file_storage import SaveFileStorage


class ListFiles(ListFilesUseCase, ListFoldersUseCase):
    def __init__(self, storage: SaveFileStorage) -> None:
        self._storage = storage

    async def list_files_in_folder(self, folder_name: str) -> list[str]:
        """Получение файлов в папке.

        :param folder_name:
        :return:
        """
        return await self._storage.list_files_in_folder(folder_name=folder_name)

    async def list_folders_in_root(self) -> list[str]:
        """Получение папок в руте.

        :return:
        """
        return await self._storage.list_folders_in_root()
