from dishka import Provider, Scope, from_context, provide
from redis.asyncio.client import Redis

from resume_service.main.config import InfrastructureSettings, Settings


class AppProvider(Provider):
    scope = Scope.APP
    settings = from_context(provides=Settings)

    @provide
    def redis(self, settings: Settings) -> Redis:
        return Redis.from_url(str(settings.INFRA.REDIS.DSN))

    @provide
    async def infra(self, settings: Settings) -> InfrastructureSettings:
        return settings.INFRA
