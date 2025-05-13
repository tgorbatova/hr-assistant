from file_storage.application.interfaces.usecase.file import GetInfoUseCase
from file_storage.domain.models.file import Folder
from file_storage.domain.repositories.file import FileReader


class GetInfoInteractor(GetInfoUseCase):
    def __init__(
        self,
        repository: FileReader,
    ) -> None:
        self._repository = repository

    async def get_folder_info(self, folder_name: str) -> Folder:
        """Получение информации о папке.

        :param folder_name:
        """
        return await self._repository.get_folder_info(folder_name)
