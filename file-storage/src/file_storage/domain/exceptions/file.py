from typing import Any


class FileError(Exception):
    """File error."""


class SaveFileError(FileError):
    """Save file error."""


class DeleteFolderError(FileError):
    """Delete folder error."""


class ReadFileError(FileError):
    """Read file error."""


class FileNotFoundError(FileError):
    """File not found."""


class SaveToDbError(SaveFileError):
    """Save to db error."""


class DeleteFromDbError(FileError):
    """Delete from db error."""


class SaveToStorageError(SaveFileError):
    """Save to storage error."""

    def __init__(self, file_path: str) -> None:
        super().__init__(f"Failed to save file to storage: {file_path}")
        self.file_path = file_path

    @property
    def details(self) -> dict[str, Any]:
        """Детали ошибки."""
        return {"file_path": self.file_path}


class ReadFromStorageError(ReadFileError):
    """Read from storage error."""

    def __init__(self, file_path: str) -> None:
        super().__init__(f"Failed to read file to storage: {file_path}")
        self.file_path = file_path

    @property
    def details(self) -> dict[str, Any]:
        """Детали ошибки."""
        return {"file_path": self.file_path}


class DeleteFromStorageError(DeleteFolderError):
    """Delete from storage error."""
