from typing import Annotated

from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter, Query
from starlette import status
from starlette.responses import StreamingResponse

from file_storage.application.interfaces.usecase.file import GetResultByIdUseCase
from file_storage.domain.exceptions.file import FileNotFoundError
from file_storage.domain.models.file import FileId
from file_storage.domain.mongo_filter.types import FromQuery
from file_storage.infrastructure.sqlalchemy.repositories.file import FileRepositoryImpl
from file_storage.presentation.fastapi.response_model import DetailedHttpException, EntityNotFoundModel
from file_storage.presentation.fastapi.schemas.file import (
    GetResultQuery,
)
from file_storage.presentation.filters.results import ResumeResultsFilter

result_router = APIRouter(prefix="/files/results", route_class=DishkaRoute)


@result_router.get(
    "/{file_id}",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": EntityNotFoundModel}},
)
async def get_results_by_file_id(
    file_id: FileId, usecase: FromDishka[GetResultByIdUseCase], queries: Annotated[GetResultQuery, Query()]
) -> StreamingResponse:
    """Получение файла по идентификатору.

    \f
    :param file_id:
    :param usecase:
    :param queries:
    :return:
    """
    try:
        return StreamingResponse(await usecase.get_result_by_file_id(file_id=file_id, type=queries.type))
    except FileNotFoundError as exc:
        raise DetailedHttpException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@result_router.get(
    "/get/filtered",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_404_NOT_FOUND: {"model": EntityNotFoundModel}},
)
async def get_filtered_results(
    repository: FromDishka[FileRepositoryImpl], filters: FromQuery[ResumeResultsFilter]
) -> StreamingResponse:
    """Получение данных из монго по фильтрам.

    \f
    :param repository:
    :param filters:
    :return:
    """
    return await repository.get_filtered(filters)
