import structlog
from dishka import FromDishka
from dishka.integrations.fastapi import DishkaRoute, inject
from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from front.infrastructure.repositories.files import FilesRepository
from front.presentation.fastapi.routes.jinja import templates

files_router = APIRouter(route_class=DishkaRoute)
_logger: structlog.stdlib.BoundLogger = structlog.get_logger(__name__)


@inject
@files_router.get("/folders")
async def get_folders(request: Request, repository: FromDishka[FilesRepository]) -> list[str]:
    """Список папок.

    \f
    :param request:
    :param repository:
    :return:
    """
    folders = await repository.get_all_folders()
    return templates.TemplateResponse("/common/files/folders.html", {"request": request, "folders": folders})


@inject
@files_router.get("/folders/{folder}")
async def get_folder(folder: str, request: Request, repository: FromDishka[FilesRepository]) -> list[str]:
    """Список папок.

    \f
    :param folder:
    :param request:
    :param repository:
    :return:
    """
    files = await repository.get_all_folder_files(folder=folder)
    return templates.TemplateResponse(
        "/common/files/folder.html", {"request": request, "folder": folder, "files": files}
    )


@inject
@files_router.get("/folders/{folder}/file/{file}")
async def get_file(folder: str, file: str, request: Request, repository: FromDishka[FilesRepository]) -> list[str]:
    """Список папок.

    \f
    :param folder:
    :param file:
    :param request:
    :param repository:
    :return:
    """
    path = f"files/{folder}/{file}"
    file_info = await repository.get_file_info(path)
    return templates.TemplateResponse("/common/files/file.html", {"request": request, "folder": folder, "file": file, "file_id": file_info["id"]})


@inject
@files_router.post("/folders/{folder}/upload")
async def upload_file(
    folder: str, file: UploadFile, request: Request = None, repository: FromDishka[FilesRepository] = None
):
    """Загрузить файл в папку."""
    try:
        # Just pass the file object directly to repository
        await repository.upload_file_to_folder(folder, file)
        return JSONResponse(
            content={"message": "File uploaded successfully", "filename": file.filename}, status_code=200
        )
    except Exception as e:
        print(f"Upload error: {e!s}")
        raise HTTPException(status_code=400, detail=str(e))
