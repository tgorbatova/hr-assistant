import enum
from typing import TypedDict


class ResultType(enum.StrEnum):
    FORMAT = "format"


class TaskResultDict(TypedDict):
    task_id: str
    status: str
