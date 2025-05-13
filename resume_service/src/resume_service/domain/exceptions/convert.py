class ConvertError(Exception):
    """Base class for exceptions in conversion module."""


class UnsupportedTypeError(ConvertError):
    """Exception raised for unsupported data types."""
