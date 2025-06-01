from pydantic import BaseModel

from resume_service.domain.models.resume_info import ResumeInfo


class ConvertedMsgSchema(BaseModel):
    file_id: str
    text: str


class FormatedMsgSchema(BaseModel):
    file_id: str
    resume: ResumeInfo
