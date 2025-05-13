from uuid import UUID

from pydantic import BaseModel


class ConvertedMsgSchema(BaseModel):
    file_id: UUID
    text: str
