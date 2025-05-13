from typing import Annotated, Any

from pydantic import BaseModel, Field
from starlette.requests import Request
from starlette.responses import JSONResponse

from file_storage.utils.fastapi import HTTPException


class ErrorResponseModel(BaseModel):
    status_code: Annotated[int, Field(examples=[400])]
    detail: Annotated[str, Field(examples=["В сервисе произошла ошибка."])]
    type: Annotated[str, Field(examples=["BaseError"])]
    details: Annotated[dict[str, Any], Field(examples=[{"error_field": "error_value"}])]


class InternalErrorModel(ErrorResponseModel):
    status_code: Annotated[int, Field(examples=[500])]


class EntityNotFoundModel(ErrorResponseModel):
    status_code: Annotated[int, Field(examples=[404])]
    detail: Annotated[str, Field(examples=["Entity not found"])]
    type: Annotated[str, Field(examples=["EntityNotFoundError"])]
    details: Annotated[dict[str, Any], Field(examples=[{"entity_id": "123"}])]


class DetailedHttpException(HTTPException):
    def __init__(
        self,
        status_code: int,
        exc_type: str = "HTTPException",
        detail: str | None = None,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(status_code=status_code, detail=detail, headers=headers, exc_type=exc_type)
        self.details = details or {}


async def detailed_exception_handler(_request: Request, exc: DetailedHttpException) -> JSONResponse:  # noqa: RUF029, RUF100
    """FastAPI Exception handler populated with detailed exception info."""
    return JSONResponse(
        {
            "message": exc.detail,
            "details": exc.details,
            "status_code": exc.status_code,
        },
        status_code=exc.status_code,
    )
