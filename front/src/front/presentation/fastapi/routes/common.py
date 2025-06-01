import structlog
from dishka.integrations.fastapi import DishkaRoute
from fastapi import APIRouter
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


@main_router.get("/dashboard")
async def dashboard_page(request: Request) -> Response:
    """Страница дашборда.

    \f
    :param request:
    :return:
    """
    return templates.TemplateResponse("/common/dashboard/dashboard.html", {"request": request})


@main_router.get("/dashboard/{folder}")
async def dashboard_page(folder: str, request: Request) -> Response:
    """Страница дашборда.

    \f
    :param folder:
    :param request:
    :return:
    """
    return templates.TemplateResponse("/common/dashboard/folder_dashboard.html", {"request": request, "folder": folder})
