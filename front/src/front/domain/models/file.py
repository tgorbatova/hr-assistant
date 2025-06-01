import datetime
from dataclasses import dataclass
from typing import Self

from front.domain.types.file import FileId


@dataclass(slots=True)
class FileMetadata:
    size: int
    name: str
    file_created_at: datetime.datetime
    path: str


@dataclass(slots=True)
class File:
    id: FileId

    metadata: FileMetadata

    @classmethod
    def create(
        cls,
        *,
        file_id: FileId,
        name: str,
        size: int,
        file_created_at: datetime.datetime,
        path: str,
    ) -> Self:
        """Создание отчета.

        :param file_id:
        :param size:
        :param name:
        :param file_created_at:
        :param path:
        :return:
        """
        return cls(
            id=file_id,
            metadata=FileMetadata(
                size=size,
                name=name,
                file_created_at=file_created_at,
                path=path,
            ),
        )
