from collections.abc import AsyncIterator

from dishka import AnyOf, Provider, Scope, alias, from_context, provide
from taskiq import AsyncBroker
from taskiq_redis import RedisAsyncResultBackend

from resume_service.main.config import InfrastructureSettings
from resume_service.presentation.worker.worker_setup import CancellableBroker, CancellableListQueueBroker


class TaskBrokerFactoryProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    async def create_broker(
        self, settings: InfrastructureSettings
    ) -> AsyncIterator[AnyOf[AsyncBroker, CancellableListQueueBroker, CancellableBroker]]:
        result_backend: RedisAsyncResultBackend = RedisAsyncResultBackend(str(settings.REDIS.DSN))
        broker = CancellableListQueueBroker(str(settings.REDIS.DSN)).with_result_backend(result_backend)
        await broker.startup()
        try:
            yield broker
        finally:
            await broker.shutdown()


class TaskBrokerContextProvider(Provider):
    scope = Scope.APP

    broker = from_context(AsyncBroker)

    cancellable = alias(AsyncBroker, provides=AnyOf[CancellableBroker, CancellableListQueueBroker])
