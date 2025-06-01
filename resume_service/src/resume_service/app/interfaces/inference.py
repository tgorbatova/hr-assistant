from typing import Protocol

from resume_service.domain.models.resume_info import ResumeInfo


class Inference(Protocol):
    async def inference(self, file_data: dict) -> ResumeInfo:
        """Инференс конвертирования."""
        ...
