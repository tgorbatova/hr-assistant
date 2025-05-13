import asyncio

import structlog

from resume_service.app.interfaces.inference import Inference
from resume_service.domain.models.message import ConvertedMsgSchema
from resume_service.domain.services.convert import ConverterService
from resume_service.domain.services.js import stream
from resume_service.main.config import Settings
from faststream.nats import NatsBroker

_logger: structlog.stdlib.BoundLogger = structlog.get_logger("inference")


class InferenceService(Inference):
    def __init__(self, settings: Settings, service: ConverterService, broker: NatsBroker) -> None:
        self.settings = settings
        self.converter_service = service
        self.broker = broker

    async def inference(self, file_data: dict) -> str:
        """Make inference."""
        _logger.debug("Got inference request, file_data=%s", file_data)
        try:
            result = await self.converter_service.convert(file_data)
            if file_data["file_id"]:
                message = ConvertedMsgSchema(
                    file_id=file_data["file_id"],
                    text=result
                )
                _logger.debug("Publishing message after converting, message=%s", message)

                await asyncio.sleep(15)

                await self.broker.connect()
                publisher = self.broker.publisher("inference.converted", stream=stream)
                await publisher.publish(message)
            return result
        except Exception as exc:  # noqa: BLE001
            await _logger.aexception("Failed to start resume inference", exc=exc)
