import uuid
from dataclasses import dataclass

from file_storage.domain.models.file import FileId
from file_storage.domain.models.result import ResultId, ResultType


@dataclass(slots=True)
class SaveResultDto:
    id: ResultId
    file_id: FileId
    type: ResultType
    size: int
    file_name: str = ""
    folder_name: str = ""
    path: str = ""

    @staticmethod
    def new_id() -> ResultId:
        """Генерация нового идентификатора.

        :return:
        """
        return ResultId(uuid.uuid4())
