import structlog
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute, inject
from fastapi import APIRouter, Request

from front.infrastructure.repositories.files import FilesRepository

results_router = APIRouter(route_class=DishkaRoute)
_logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@inject
@results_router.get("/results/{folder}")
async def get_folders(folder: str, request: Request, repository: FromDishka[FilesRepository]) -> dict:
    """Список папок.

    \f
    :param folder:
    :param request:
    :param repository:
    :return:
    """
    return await repository.get_results_by_folder(folder=folder)
