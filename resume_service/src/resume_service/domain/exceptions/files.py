class FilesError(Exception):
    """Base class for exceptions in files module."""


class GetFileError(FilesError):
    """Exception raised when a file is not found."""
