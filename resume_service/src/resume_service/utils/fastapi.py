from fastapi.exceptions import HTTPException as FastAPIHTTPException
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse


class HTTPException(FastAPIHTTPException):
    def __init__(
        self,
        status_code: int,
        exc_type: str = "HTTPException",
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.type = exc_type


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:  # noqa: RUF029
    """Handle http exceptions."""
    return JSONResponse(
        {
            "message": exc.detail,
            "type": exc.type,
            "status_code": exc.status_code,
        },
        status_code=exc.status_code,
    )


async def exception_handler(_request: Request, exc: Exception) -> JSONResponse:  # noqa: RUF029
    """Handle exceptions raised by FastAPI."""
    message = getattr(exc, "args", exc)
    return JSONResponse(
        {
            "message": f'Unhandled exception: "{message}"',
            "type": exc.__class__.__name__,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
        status_code=500,
    )
