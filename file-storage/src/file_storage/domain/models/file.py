import datetime
import uuid
from dataclasses import dataclass
from typing import NewType, Self

import structlog

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("domain.file")

FileId = NewType("FileId", uuid.UUID)
FolderId = NewType("FolderId", uuid.UUID)


@dataclass(slots=True)
class FileMetadata:
    size: int
    name: str
    file_name: str
    folder_name: str
    file_created_at: datetime.datetime
    path: str


@dataclass(slots=True)
class File:
    id: FileId

    metadata: FileMetadata

    @staticmethod
    def new_id() -> FileId:
        """Генерация нового идентификатора.

        :return:
        """
        file_id = FileId(uuid.uuid4())
        _logger.debug("New file id generated", file_id=file_id)
        return file_id

    @classmethod
    def create(
        cls,
        *,
        file_id: FileId,
        name: str,
        file_name: str,
        folder_name: str,
        size: int,
        file_created_at: datetime.datetime,
        path: str,
    ) -> Self:
        """Создание отчета.

        :param file_id:
        :param size:
        :param name:
        :param file_name:
        :param folder_name:
        :param file_created_at:
        :param path:
        :return:
        """
        return cls(
            id=file_id,
            metadata=FileMetadata(
                size=size,
                name=name,
                file_name=file_name,
                folder_name=folder_name,
                file_created_at=file_created_at,
                path=path,
            ),
        )


@dataclass(slots=True)
class Folder:
    id: FolderId
    name: str
    description: str

    @staticmethod
    def new_id() -> FolderId:
        """Генерация нового идентификатора.

        :return:
        """
        folder_id = FolderId(uuid.uuid4())
        _logger.debug("New folder id generated", file_id=folder_id)
        return folder_id

    @classmethod
    def create(cls, *, folder_id: FolderId, name: str, description: str) -> Self:
        """Создание папки.

        :param folder_id:
        :param name:
        :param description:
        :return:
        """
        return cls(id=folder_id, name=name, description=description)


@dataclass(slots=True)
class SaveFile:
    id: FileId
    file_name: str
    name: str
    folder_name: str | None
    size: int
    file_path: str


@dataclass(slots=True)
class SaveFolder:
    id: FolderId
    name: str
    description: str = ""
