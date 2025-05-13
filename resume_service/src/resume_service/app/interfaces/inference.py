from typing import Protocol

from resume_service.domain.models.message import ConvertedMsgSchema


class Inference(Protocol):
    async def inference(self, file_data: dict) -> str:
        """Инференс конвертирования."""
        ...
