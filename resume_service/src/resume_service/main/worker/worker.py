import structlog
from dishka import make_async_container
from dishka.integrations.taskiq import TaskiqProvider, setup_dishka
from faststream.nats import NatsBroker
from taskiq import AsyncBroker, TaskiqEvents, TaskiqState
from taskiq_redis import RedisAsyncResultBackend

from resume_service.di.factory import base_providers
from resume_service.di.providers.task_broker import TaskBrokerContextProvider
from resume_service.di.providers.worker import WorkerProvider
from resume_service.main.config import Settings, settings
from resume_service.presentation.worker.middleware import TaskStatusMiddleware
from resume_service.presentation.worker.tasks import register_tasks
from resume_service.presentation.worker.worker_setup import CancellableListQueueBroker, CancellableReceiver
from resume_service.utils.logging import setup_logging

broker_logger: structlog.stdlib.BoundLogger = structlog.get_logger("resume_service.broker")

taskiq_broker = CancellableListQueueBroker(str(settings.INFRA.REDIS.DSN)).with_result_backend(
    RedisAsyncResultBackend(str(settings.INFRA.REDIS.DSN))
)

Receiver = CancellableReceiver

register_tasks(taskiq_broker)

broker = NatsBroker(
    str(settings.INFRA.NATS.DSN),
    logger=broker_logger,
)

container = make_async_container(
    *base_providers,
    TaskiqProvider(),
    TaskBrokerContextProvider(),
    WorkerProvider(),
    context={Settings: settings, AsyncBroker: taskiq_broker, NatsBroker: broker},
)

setup_dishka(container, taskiq_broker)

taskiq_broker.add_middlewares(TaskStatusMiddleware(connection_pool=taskiq_broker.connection_pool))


@taskiq_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def startup(_: TaskiqState) -> None:
    """Broker startup."""
    setup_logging(
        service_name=settings.SERVICE_NAME + ".worker",
        json_logs=settings.JSON_LOGGING,
        unwanted_loggers=["python_multipart.multipart"],
        custom_processors=[
            structlog.processors.CallsiteParameterAdder({
                structlog.processors.CallsiteParameter.THREAD,
                structlog.processors.CallsiteParameter.PROCESS,
            }),
        ],
    )
