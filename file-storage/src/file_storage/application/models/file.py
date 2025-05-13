from dataclasses import dataclass

from file_storage.domain.models.file import FileId, FolderId


@dataclass(slots=True)
class SaveFileDto:
    id: FileId
    size: int
    name: str
    file_name: str = ""
    folder: str | None = None
    file_path: str = ""


@dataclass(slots=True)
class SaveFolderDto:
    id: FolderId
    name: str
    description: str = ""
