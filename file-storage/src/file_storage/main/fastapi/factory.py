from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import structlog
from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka
from dishka.integrations.faststream import setup_dishka as setup_dishka_faststream
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse
from faststream.nats import NatsBroker
from starlette import status
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from file_storage.main.config import DB_SCHEMA, InfraSettings, Settings, settings
from file_storage.main.di.app import AppProvider
from file_storage.main.di.infrastructure import InfrastructureProvider
from file_storage.presentation.broker.routes.result import results_router
from file_storage.presentation.fastapi.response_model import (
    DetailedHttpException,
    InternalErrorModel,
    detailed_exception_handler,
)
from file_storage.presentation.fastapi.router import router
from file_storage.presentation.fastapi.routes.results import result_router
from file_storage.utils.fastapi import HTTPException, exception_handler, http_exception_handler
from file_storage.utils.logging import StructLoggingMiddleware, setup_logging

logger: structlog.stdlib.BoundLogger = structlog.get_logger("main")

app_logger: structlog.stdlib.BoundLogger = structlog.get_logger("fs.app")
broker_logger: structlog.stdlib.BoundLogger = structlog.get_logger("fs.broker")

broker = NatsBroker(
    str(settings.INFRA.NATS.DSN),
    logger=broker_logger,
)

container = make_async_container(
    AppProvider(),
    InfrastructureProvider(),
    context={Settings: settings, InfraSettings: settings.INFRA, NatsBroker: broker},
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:  # noqa: ARG001, RUF100  # pragma: no cover
    """Жизненный цикл приложения.

    :param app:
    """
    setup_dishka_faststream(container, broker=broker, finalize_container=False, auto_inject=True)

    broker.include_router(results_router)

    await broker.start()

    yield

    await broker.close()


def create_fastapi_app() -> FastAPI:
    """Создание FastAPI приложения.

    :return:
    """
    app = FastAPI(
        title="HR Assistant File Storage Service",
        description="Сервис для работы с вакансиями и резюме.",
        version="1.0.0",
        default_response_class=ORJSONResponse,
        middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_headers=["*"],
                allow_methods=["*"],
                allow_credentials=True,
            ),
            Middleware(StructLoggingMiddleware),
        ],
        exception_handlers={
            DetailedHttpException: detailed_exception_handler,
            HTTPException: http_exception_handler,
            Exception: exception_handler,
        },
        responses={
            status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": InternalErrorModel},
        },
        lifespan=lifespan,
    )

    app.include_router(router)
    app.include_router(result_router)

    setup_logging(
        settings.APP_NAME,
        json_logs=settings.LOGGING.JSON_LOGGING,
        custom_processors=[
            structlog.processors.CallsiteParameterAdder({
                structlog.processors.CallsiteParameter.PROCESS,
            }),
        ],
        unwanted_loggers=["python_multipart.multipart", "botocore", "pymongo"],
        log_level=settings.LOGGING.LEVEL,
    )

    logger.info("Settings loaded with DB_SCHEMA %s", DB_SCHEMA, db_schema=DB_SCHEMA)

    return app


def create_app() -> FastAPI:
    """Создание FastAPI приложения c внешними зависимостями.

    :return:
    """
    app = create_fastapi_app()
    setup_dishka(container, app)

    return app
