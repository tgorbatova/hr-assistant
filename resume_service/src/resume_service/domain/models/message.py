from pydantic import BaseModel


class ConvertedMsgSchema(BaseModel):
    file_id: str
    text: str
