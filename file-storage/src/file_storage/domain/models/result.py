import datetime
import enum
import uuid
from dataclasses import dataclass
from typing import NewType, Self

import structlog

from file_storage.domain.models.file import FileId

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("domain.file")

ResultId = NewType("ResultId", uuid.UUID)


class ResultType(enum.Enum):
    FORMAT = "FORMAT"


@dataclass(slots=True)
class ResultMetadata:
    size: int
    type: ResultType
    file_name: str
    folder_name: str
    file_created_at: datetime.datetime
    path: str


@dataclass(slots=True)
class Result:
    id: ResultId
    file_id: FileId

    metadata: ResultMetadata

    @staticmethod
    def new_id() -> ResultId:
        """Генерация нового идентификатора.

        :return:
        """
        result_id = ResultId(uuid.uuid4())
        _logger.debug("New result id generated", result_id=result_id)
        return result_id

    @classmethod
    def create(
        cls,
        *,
        result_id: ResultId,
        file_id: FileId,
        file_name: str,
        folder_name: str,
        size: int,
        file_created_at: datetime.datetime,
        path: str,
        type: ResultType,
    ) -> Self:
        """Создание отчета.

        :param result_id:
        :param file_id:
        :param size:
        :param folder_name:
        :param file_name:
        :param file_created_at:
        :param path:
        :param type:
        :return:
        """
        return cls(
            id=result_id,
            file_id=file_id,
            metadata=ResultMetadata(
                size=size,
                folder_name=folder_name,
                file_name=file_name,
                file_created_at=file_created_at,
                path=path,
                type=type,
            ),
        )


@dataclass(slots=True)
class SaveResult:
    id: ResultId
    file_id: FileId
    type: ResultType
    file_name: str
    path: str
    folder_name: str
    size: int
