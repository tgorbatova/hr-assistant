import functools
import logging
from collections.abc import Callable
from time import monotonic
from typing import Any

import orjson
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from structlog.typing import EventDict, Processor

logger: structlog.stdlib.BoundLogger = structlog.get_logger("base_logger")

_unwanted_loggers: list[str] = [
    "httpcore",
    "httpx",
    "uvicorn.access",
    "urllib3.connectionpool",
    "multipart",
    "multipart.multipart",
]


def rename_event_key(_: structlog.BoundLogger, __: str, event_dict: EventDict) -> EventDict:
    """Rename event key.

    Log entries keep the text message in the `event` field, but Datadog
    uses the `message` field. This processor moves the value from one field to
    the other.
    See https://github.com/hynek/structlog/issues/35#issuecomment-591321744
    """
    event_dict["message"] = event_dict.pop("event")
    return event_dict


def set_service_name(_: structlog.BoundLogger, __: str, event_dict: EventDict, *, service_name: str) -> EventDict:
    """Set service name."""
    event_dict["service"] = service_name
    return event_dict


def serializer(message: dict[str, Any], default: Callable[[Any], str] | None = None) -> str:
    """Serialize a message."""
    message["level"] = message["level"].upper()
    message["time"] = message["timestamp"]
    if file_name := message.pop("filename", None):
        message["file"] = file_name
    if func_name := message.pop("func_name", None):
        message["function"] = func_name
    if line_no := message.pop("lineno", None):
        message["line"] = line_no
    return orjson.dumps(message, default=default).decode()


def remove_unwanted_args_in_console(
    _: structlog.BoundLogger, __: str, event_dict: EventDict, *, unwanted: list[str]
) -> EventDict:
    """Remove unwanted args from console."""
    for arg in unwanted:
        event_dict.pop(arg, None)
    return event_dict


def setup_logging(
    service_name: str,
    *,
    json_logs: bool = False,
    log_level: str = "DEBUG",
    unwanted_loggers: list[str] | None = None,
    unwanted_extras: list[str] | None = None,
    custom_processors: list[Processor] | None = None,
    custom_stdlib_filters: list[logging.Filter] | None = None,
) -> None:
    """Set up logging."""
    if unwanted_extras is None:
        unwanted_extras = []

    if custom_processors is None:
        custom_processors = []

    if custom_stdlib_filters is None:
        custom_stdlib_filters = []

    timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False)

    shared_processors: list[Processor] = [
        timestamper,
        functools.partial(set_service_name, service_name=service_name),
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.stdlib.ExtraAdder(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.CallsiteParameterAdder({
            structlog.processors.CallsiteParameter.FILENAME,
            structlog.processors.CallsiteParameter.FUNC_NAME,
            structlog.processors.CallsiteParameter.LINENO,
        }),
    ]
    shared_processors.extend(custom_processors)

    if json_logs:
        shared_processors.append(rename_event_key)  # noqa: FURB113
        shared_processors.append(structlog.processors.format_exc_info)
    else:
        shared_processors.append(functools.partial(remove_unwanted_args_in_console, unwanted=unwanted_extras))

    structlog.configure(
        processors=shared_processors  # noqa: RUF005
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
        wrapper_class=structlog.make_filtering_bound_logger(logging.NOTSET),
    )

    log_renderers: list[structlog.types.Processor]
    if json_logs:
        log_renderers = [structlog.processors.JSONRenderer(serializer=serializer)]
    else:
        log_renderers = [structlog.dev.ConsoleRenderer()]

    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            *log_renderers,
        ],
    )

    handler = logging.StreamHandler()
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level.upper())

    for filter_ in custom_stdlib_filters:
        handler.addFilter(filter_)

    handler.setFormatter(formatter)

    for _log in ["uvicorn", "uvicorn.error"]:
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = True

    if unwanted_loggers:
        _unwanted_loggers.extend(unwanted_loggers)

    for _log in _unwanted_loggers:
        logging.getLogger(_log).handlers.clear()
        logging.getLogger(_log).propagate = False


_logger = structlog.get_logger("response")


class StructLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware для структурированного логирования запросов и ответов."""

    @staticmethod
    async def dispatch(request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Обрабатывает запрос, логирует ответ и освобождает контекстные переменные.

        :param request: Входящий HTTP-запрос.
        :param call_next: Функция для вызова следующего middleware или обработчика.
        :return: HTTP-ответ.
        """
        start = monotonic()

        response = await call_next(request)

        duration = monotonic() - start

        await _logger.ainfo(
            f"Response handled in {duration:.3f} s: {request.method} {request.url.path} {response.status_code}",
            status=response.status_code,
            duration=duration,
            method=request.method,
            request_uri=request.url.path,
            status_code=response.status_code,
        )

        structlog.contextvars.unbind_contextvars("request_id", "correlation_id", "user_id")

        return response
