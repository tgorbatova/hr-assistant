from collections.abc import AsyncIterator

import structlog
from dishka import Provider, Scope, provide
from faststream.nats import NatsBroker

from resume_service.main.config import Settings


class BrokerFactoryProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    async def create_broker(self, settings: Settings) -> AsyncIterator[NatsBroker]:
        broker_logger: structlog.stdlib.BoundLogger = structlog.get_logger("fs.broker")

        faststream_broker = NatsBroker(str(settings.INFRA.NATS.DSN), logger=broker_logger)

        await faststream_broker.start()

        try:
            yield faststream_broker
        finally:
            await faststream_broker.close()
