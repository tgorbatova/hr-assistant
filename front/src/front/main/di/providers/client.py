from dishka import AnyOf, Provider, Scope, provide
from nats.aio.client import Client as NatsClient
from nats.js import JetStreamContext
from nats.js.api import StreamConfig, RetentionPolicy, StreamSource

from front.domain.types.clients import FilesRequestClient
from front.main.config import settings
from front.presentation.broker.socket import SocketManager
from front.utils.client import BaseHttpClient


class ClientProvider(Provider):
    scope = Scope.APP

    @provide
    async def files_client(self) -> AnyOf[FilesRequestClient, BaseHttpClient]:
        return BaseHttpClient(
            base_url=str(settings.INFRA.CLIENT.FILES.BASE_URL).rstrip("/") + settings.INFRA.CLIENT.FILES.DOMAIN
        )

    @provide(scope=Scope.APP)
    async def provide_nats(self) -> NatsClient:
        nc = NatsClient()
        await nc.connect(str(settings.INFRA.NATS.DSN))
        return nc
