
import structlog
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute, inject
from fastapi import APIRouter, WebSocket
from starlette.requests import Request
from starlette.responses import Response

from front.presentation.fastapi.routes.jinja import templates

main_router = APIRouter(route_class=DishkaRoute)
_logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@main_router.get("/")
async def main_page(request: Request) -> Response:
    """Страница главного экрана.

    \f
    :param request:
    :return:
    """
    return templates.TemplateResponse("/common/index/page.html", {"request": request})

