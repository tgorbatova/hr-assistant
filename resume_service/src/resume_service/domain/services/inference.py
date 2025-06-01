import structlog
from faststream.nats import NatsBroker

from resume_service.app.interfaces.inference import Inference
from resume_service.domain.models.message import ConvertedMsgSchema, FormatedMsgSchema
from resume_service.domain.models.resume_info import ResumeInfo
from resume_service.domain.services.convert import ConverterService
from resume_service.domain.services.js import stream
from resume_service.infrastructure.adapters.llm import LLMAdapter
from resume_service.main.config import Settings

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("inference")


class InferenceService(Inference):
    def __init__(self, settings: Settings, service: ConverterService, llm_repo: LLMAdapter, broker: NatsBroker) -> None:
        self.settings = settings
        self.converter_service = service
        self.broker = broker
        self.llm_repo = llm_repo

    async def inference(self, file_data: dict) -> ResumeInfo:
        """Make inference."""
        _logger.debug("Got inference request, file_data=%s", file_data)
        try:
            result = await self.converter_service.convert(file_data)
            if file_data["file_id"]:
                message = ConvertedMsgSchema(file_id=file_data["file_id"], text=result)
                _logger.debug("Publishing message after converting, message=%s", message)
                await self.broker.connect()
                publisher = self.broker.publisher("inference.converted", stream=stream)
                await publisher.publish(message)

            formatted_resume = await self.llm_repo.format_resume(result)
            if file_data["file_id"]:
                message = FormatedMsgSchema(file_id=file_data["file_id"], resume=formatted_resume)
                _logger.debug("Publishing message after formatting, message=%s", message)
                await self.broker.connect()
                publisher = self.broker.publisher("inference.formatted", stream=stream)
                await publisher.publish(message)

            return formatted_resume
        except Exception as exc:  # noqa: BLE001
            await _logger.aexception("Failed to complete resume inference", exc=exc)
