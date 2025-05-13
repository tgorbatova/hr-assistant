import enum


class TaskStatus(enum.StrEnum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    NOT_FOUND = "not_found"
    CANCELLED = "cancelled"
