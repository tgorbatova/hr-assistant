from file_storage.application.interfaces.usecase.file import CreateFolderUseCase
from file_storage.application.models.file import SaveFolderDto
from file_storage.domain.models.file import FolderId, SaveFolder
from file_storage.domain.repositories.file import FileRepository
from file_storage.domain.repositories.file_storage import SaveFileStorage


class CreateInteractor(CreateFolderUseCase):
    def __init__(
        self,
        repository: FileRepository,
        storage: SaveFileStorage,
    ) -> None:
        self._repository = repository
        self._storage = storage

    async def create_folder(self, folder_info: SaveFolderDto) -> FolderId:
        """Создание папки.

        :param folder_info:
        """
        save_folder = SaveFolder(id=folder_info.id, name=folder_info.name, description=folder_info.description)
        folder_id = await self._repository.create_folder(save_folder)

        await self._storage.create_folder(save_folder)

        return folder_id
