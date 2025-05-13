from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from file_storage.domain.models.file import File, FileId, Folder, FolderId
from file_storage.domain.models.result import ResultType


class SaveFileQuery(BaseModel):
    file_id: Annotated[
        FileId,
        Query(
            default_factory=File.new_id,
            description="Идентификатор файла. Если не передавать явно, то генерируется случайный UUID4.",
        ),
    ]
    folder: Annotated[
        str,
        Query(
            default=None,
            description="Название 'папки'. Если не передавать явно, то файл будет помещен в корневую папку.",
        ),
    ]
    name: Annotated[
        str,
        Query(
            default=None,
            description="Название файла (резюме).",
        ),
    ]


class GetFilesQuery(BaseModel):
    folder: Annotated[
        str,
        Query(
            description="Название 'папки'.",
        ),
    ]


class CreateFolderQuery(BaseModel):
    folder_id: Annotated[
        FolderId,
        Query(
            default_factory=Folder.new_id,
            description="Идентификатор папки. Если не передавать явно, то генерируется случайный UUID4.",
        ),
    ]


class GetFolderQuery(BaseModel):
    name: Annotated[
        str,
        Query(
            description="Название папки",
        ),
    ]


class GetFileQuery(BaseModel):
    path: Annotated[
        str,
        Query(
            description="Путь до файла",
        ),
    ]


class GetResultQuery(BaseModel):
    type: Annotated[
        ResultType,
        Query(
            description="Тип результата.",
        ),
    ]
