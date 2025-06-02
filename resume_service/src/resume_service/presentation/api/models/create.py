from typing import Annotated

from fastapi import Query
from pydantic import BaseModel

from resume_service.presentation.broker.models.file import FileId


class CreateTaskQuery(BaseModel):
    file_id: Annotated[
        FileId,
        Query(
            default=None,
            description="Идентификатор файла.",
        ),
    ]


class ChatQuery(BaseModel):
    question: Annotated[
        str,
        Query(
            description="Вопрос",
        ),
    ]
    resume: Annotated[
        dict,
        Query(
            description="Резюме",
        ),
    ]
