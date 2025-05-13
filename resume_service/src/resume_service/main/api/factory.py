from contextlib import asynccontextmanager
from typing import Any

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka as setup_dishka_fastapi
from fastapi import FastAPI

from resume_service.di.factory import base_providers
from resume_service.di.providers.app import AppProvider
from resume_service.di.providers.client import InfrastructureProvider
from resume_service.di.providers.service import ServiceProvider
from resume_service.di.providers.task_broker import TaskBrokerFactoryProvider
from resume_service.main.config import Settings, settings
from resume_service.presentation.api.router import router
from resume_service.presentation.broker.routes.pipeline import inference_router
from resume_service.utils.fastapi import HTTPException, exception_handler, http_exception_handler
from resume_service.utils.logging import StructLoggingMiddleware, setup_logging
from collections.abc import AsyncGenerator
import structlog
from faststream.nats import NatsBroker
from faststream import FastStream
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream

app_logger: structlog.stdlib.BoundLogger = structlog.get_logger("resume_service.app")
broker_logger: structlog.stdlib.BoundLogger = structlog.get_logger("resume_service.broker")

broker = NatsBroker(
    str(settings.INFRA.NATS.DSN),
    logger=broker_logger,
)

container = make_async_container(
        *base_providers, TaskBrokerFactoryProvider(), ServiceProvider(), context={Settings: settings, NatsBroker: broker}
    )

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:  # noqa: ARG001, RUF100  # pragma: no cover
    """Жизненный цикл приложения.

    :param app:
    """
    faststream_app = FastStream(broker, logger=app_logger)
    setup_dishka_faststream(container, faststream_app, auto_inject=True)

    broker.include_router(inference_router)

    await broker.start()

    yield

    await broker.close()

def create_app() -> FastAPI:
    """Создание приложения.

    :return: приложение
    """
    setup_logging(service_name=settings.SERVICE_NAME, json_logs=settings.JSON_LOGGING)

    app = FastAPI(
        title="Resume Converter API",
        version="1.0.0",
        exception_handlers={
            HTTPException: http_exception_handler,
            Exception: exception_handler,
            ExceptionGroup: exception_handler,
        },
        root_path="/resume-converter/api/v1",
        lifespan=lifespan
    )
    app.include_router(router)
    app.add_middleware(StructLoggingMiddleware)


    setup_dishka_fastapi(container, app)

    return app
