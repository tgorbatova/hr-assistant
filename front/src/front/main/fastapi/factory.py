from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import structlog
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI, Request
from nats.aio.client import Client as NatsClient
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from front.main.config import settings
from front.main.di.factory import container
from front.presentation.broker.manager import NATSManager
from front.presentation.broker.socket import SocketManager
from front.presentation.fastapi.router import router
from front.utils.logging import StructLoggingMiddleware, setup_logging

logger: structlog.stdlib.BoundLogger = structlog.get_logger("front")

socket_manager = SocketManager()
socket_manager.setup_handlers()


async def start_listener(app: FastAPI) -> None:
    async with container() as request_container:
        nats_client: NatsClient = await request_container.get(NatsClient)

        handler = NATSManager(nats_client, socket_manager)
        await handler.subscribe()


def setup_dependencies(app: FastAPI) -> None:
    """Настройка зависимостей.

    :param app: приложение
    """
    # setup Jinja
    staticfiles = StaticFiles(directory=settings.APP.STATICFILES_DIRECTORY)
    app.mount("/static", staticfiles, name="static")

    setup_dishka(container, app)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Жизненный цикл приложения.

    :param app: приложение
    """
    await start_listener(app)
    yield


def create_app() -> FastAPI:
    """Создание приложения.

    :return: приложение
    """
    app = FastAPI(
        title="HR Assistant front API",
        docs_url="/front/api/v1/docs",
        openapi_url="/front/api/v1/openapi.json",
        lifespan=lifespan,
    )

    # Add CORS middleware first
    origins = [
        "http://localhost:8001",
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=86400,
    )

    # Add other middleware
    app.add_middleware(StructLoggingMiddleware)

    # Include the router first
    app.include_router(router)
    
    # Setup static files
    staticfiles = StaticFiles(directory=settings.APP.STATICFILES_DIRECTORY)
    app.mount("/static", staticfiles, name="static")

    # Mount socket.io at a specific path
    socket_app = socket_manager.get_socket_app()
    app.mount("/socket.io", socket_app)

    setup_logging(
        settings.APP_NAME,
        json_logs=settings.LOGGING.JSON_LOGGING,
        custom_processors=[
            structlog.processors.CallsiteParameterAdder({
                structlog.processors.CallsiteParameter.PROCESS,
            }),
        ],
        unwanted_loggers=["python_multipart.multipart", "botocore"],
        log_level=settings.LOGGING.LEVEL,
    )

    setup_dependencies(app)

    return app
